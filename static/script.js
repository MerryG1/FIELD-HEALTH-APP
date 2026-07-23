function analyzeField() {
    const multispectral = document.getElementById("multispectral").files[0];
    const chm = document.getElementById("chm").files[0];
    const dsm = document.getElementById("dsm").files[0];
    const dtm = document.getElementById("dtm").files[0];

    if (!multispectral) {
        alert("Please upload the RGB/NIR multispectral raster.");
        return;
    }

    if (!chm && (!dsm || !dtm)) {
        alert("Upload either CHM, or both DSM and DTM.");
        return;
    }

    const formData = new FormData();
    formData.append("multispectral", multispectral);
    if (chm) formData.append("chm", chm);
    if (dsm) formData.append("dsm", dsm);
    if (dtm) formData.append("dtm", dtm);

    const btn = document.getElementById("analyze-btn");
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    const progressLabel = document.getElementById("progress-label");
    const resultEl = document.getElementById("result");

    // Disable button and show progress
    btn.disabled = true;
    progressContainer.style.display = "block";
    progressBar.value = 0;
    progressLabel.textContent = "Uploading...";
    resultEl.textContent = "";

    const xhr = new XMLHttpRequest();

    // Track upload progress (bytes sent to server)
    xhr.upload.addEventListener("progress", function (e) {
        if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100);
            progressBar.value = pct;
            progressLabel.textContent = "Uploading: " + pct + "%";
        }
    });

    // Upload finished — server is now processing
    xhr.upload.addEventListener("load", function () {
        progressBar.value = 100;
        progressLabel.textContent = "Analysing on server...";
    });

    // Response received
    xhr.addEventListener("load", function () {
        btn.disabled = false;
        progressContainer.style.display = "none";
        try {
            const data = JSON.parse(xhr.responseText);
            resultEl.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            resultEl.textContent = "Error: could not parse server response (status " + xhr.status + ")";
        }
    });

    // Network failure
    xhr.addEventListener("error", function () {
        btn.disabled = false;
        progressContainer.style.display = "none";
        resultEl.textContent = "Error: network failure — could not reach server.";
    });

    // Timeout
    xhr.addEventListener("timeout", function () {
        btn.disabled = false;
        progressContainer.style.display = "none";
        resultEl.textContent = "Error: request timed out. Your files may be too large or the server is busy.";
    });

    xhr.open("POST", "/analyze");
    xhr.timeout = 300000; // 5 minute timeout for large files
    xhr.send(formData);
}