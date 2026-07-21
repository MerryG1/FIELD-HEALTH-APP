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

    if (chm) {
        formData.append("chm", chm);
    }

    if (dsm) {
        formData.append("dsm", dsm);
    }

    if (dtm) {
        formData.append("dtm", dtm);
    }

    fetch("/analyze", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("result").textContent =
            JSON.stringify(data, null, 2);
    })
    .catch(error => {
        document.getElementById("result").textContent =
            "Error: " + error;
    });
}