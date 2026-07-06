"""
app.py
-----------
Main Flask application entry point for the
AI Resume Analyzer & Career Assistant.
"""

import os
import uuid
import io

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from config import Config, ensure_directories
from utils import (
    allowed_file,
    extract_text_from_pdf,
    analyze_resume_with_gemini,
    init_db,
    save_analysis,
    get_analysis,
    get_all_analyses,
    generate_text_report,
)


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(Config)

    ensure_directories()
    init_db()

    # ----------------------------------------------------------------
    # Routes
    # ----------------------------------------------------------------

    @app.route("/")
    def index():
        """Landing page."""
        return render_template("index.html", app_name=Config.APP_NAME)

    @app.route("/dashboard")
    def dashboard():
        """Upload dashboard + recent analysis history."""
        history = get_all_analyses(limit=10)
        return render_template(
            "dashboard.html", app_name=Config.APP_NAME, history=history
        )

    @app.route("/analyze", methods=["POST"])
    def analyze():
        """Handle resume upload, extraction, and Gemini analysis."""
        if "resume" not in request.files:
            flash("No file part in the request.", "danger")
            return redirect(url_for("dashboard"))

        file = request.files["resume"]

        if file.filename == "":
            flash("Please choose a PDF resume to upload.", "danger")
            return redirect(url_for("dashboard"))

        if not allowed_file(file.filename):
            flash("Only PDF files are supported. Please upload a .pdf resume.", "danger")
            return redirect(url_for("dashboard"))

        # Save securely with a unique name to avoid collisions
        original_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{original_name}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)

        try:
            file.save(save_path)

            resume_text = extract_text_from_pdf(save_path)
            analysis = analyze_resume_with_gemini(resume_text)
            new_id = save_analysis(original_name, analysis)

        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("dashboard"))
        except RuntimeError as exc:
            flash(str(exc), "danger")
            return redirect(url_for("dashboard"))
        except Exception as exc:  # noqa: BLE001
            flash(f"An unexpected error occurred: {exc}", "danger")
            return redirect(url_for("dashboard"))
        finally:
            # Clean up the uploaded PDF; we only persist the analysis
            if os.path.exists(save_path):
                os.remove(save_path)

        return redirect(url_for("result", analysis_id=new_id))

    @app.route("/result/<int:analysis_id>")
    def result(analysis_id):
        """Display the full analysis result for a given record."""
        record = get_analysis(analysis_id)
        if record is None:
            flash("Analysis not found. It may have been removed.", "warning")
            return redirect(url_for("dashboard"))

        return render_template(
            "result.html",
            app_name=Config.APP_NAME,
            record=record,
            analysis=record["analysis"],
        )

    @app.route("/download/<int:analysis_id>")
    def download_report(analysis_id):
        """Generate and stream a plain-text report for download."""
        record = get_analysis(analysis_id)
        if record is None:
            flash("Analysis not found.", "warning")
            return redirect(url_for("dashboard"))

        report_text = generate_text_report(record["analysis"], record["filename"])
        buffer = io.BytesIO(report_text.encode("utf-8"))
        buffer.seek(0)

        download_name = f"resume_report_{analysis_id}.txt"
        return send_file(
            buffer,
            mimetype="text/plain",
            as_attachment=True,
            download_name=download_name,
        )

    @app.route("/api/health")
    def health_check():
        """Simple JSON health check endpoint."""
        return jsonify({"status": "ok", "app": Config.APP_NAME})

    # ----------------------------------------------------------------
    # Error handlers
    # ----------------------------------------------------------------

    @app.errorhandler(404)
    def not_found_error(error):
        return (
            render_template(
                "error.html",
                app_name=Config.APP_NAME,
                error_code=404,
                error_title="Page Not Found",
                error_message="The page you are looking for does not exist or has been moved.",
            ),
            404,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(error):
        flash("File is too large. Maximum upload size is 8 MB.", "danger")
        return redirect(url_for("dashboard"))

    @app.errorhandler(500)
    def internal_error(error):
        return (
            render_template(
                "error.html",
                app_name=Config.APP_NAME,
                error_code=500,
                error_title="Internal Server Error",
                error_message="Something went wrong on our end. Please try again shortly.",
            ),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)
