/**
 * main.js
 * ---------------------------------------------------------------
 * Handles:
 *   - Drag & drop resume upload
 *   - Client-side file validation (type + size)
 *   - Loading spinner + fake progress animation during analysis
 * ---------------------------------------------------------------
 */

document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  if (!dropzone) return; // Not on the dashboard page

  const fileInput = document.getElementById("resumeInput");
  const browseBtn = document.getElementById("browseBtn");
  const removeFileBtn = document.getElementById("removeFileBtn");
  const uploadForm = document.getElementById("uploadForm");

  const stateIdle = document.getElementById("dropzoneIdle");
  const stateFile = document.getElementById("dropzoneFile");
  const stateLoading = document.getElementById("dropzoneLoading");

  const fileNameEl = document.getElementById("fileName");
  const fileSizeEl = document.getElementById("fileSize");
  const progressBar = document.getElementById("uploadProgress");

  const MAX_MB = window.MAX_UPLOAD_MB || 8;
  const MAX_BYTES = MAX_MB * 1024 * 1024;

  function bytesToReadable(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function showState(state) {
    [stateIdle, stateFile, stateLoading].forEach((el) => el.classList.add("d-none"));
    state.classList.remove("d-none");
  }

  function validateFile(file) {
    if (!file) return false;

    const isPdf =
      file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      alert("Only PDF files are supported. Please choose a .pdf resume.");
      return false;
    }

    if (file.size > MAX_BYTES) {
      alert(`File is too large. Maximum allowed size is ${MAX_MB}MB.`);
      return false;
    }

    return true;
  }

  function handleFile(file) {
    if (!validateFile(file)) return;

    fileNameEl.textContent = file.name;
    fileSizeEl.textContent = bytesToReadable(file.size);
    showState(stateFile);
  }

  // Assign chosen/dropped file to the actual input using DataTransfer
  function assignFileToInput(file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
  }

  // --- Browse button ---
  browseBtn.addEventListener("click", () => fileInput.click());

  // --- File input change ---
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFile(fileInput.files[0]);
    }
  });

  // --- Remove file ---
  removeFileBtn.addEventListener("click", () => {
    fileInput.value = "";
    showState(stateIdle);
  });

  // --- Drag & drop events ---
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      assignFileToInput(file);
      handleFile(file);
    }
  });

  // Clicking the dropzone (when idle) opens the file browser too
  dropzone.addEventListener("click", (e) => {
    const isIdleVisible = !stateIdle.classList.contains("d-none");
    if (isIdleVisible && e.target === dropzone) {
      fileInput.click();
    }
  });

  // --- Form submit: show loading state + fake progress ---
  uploadForm.addEventListener("submit", (e) => {
    if (!fileInput.files || fileInput.files.length === 0) {
      e.preventDefault();
      alert("Please select a resume PDF before analyzing.");
      return;
    }

    showState(stateLoading);

    let progress = 0;
    const interval = setInterval(() => {
      // Ease towards 90% while waiting for the server response
      progress += Math.random() * 8;
      if (progress >= 90) {
        progress = 90;
        clearInterval(interval);
      }
      progressBar.style.width = `${progress}%`;
    }, 300);
  });
});
