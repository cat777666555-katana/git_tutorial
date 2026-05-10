function highlightCurrentPage() {
  const path = location.pathname.split('/').pop();
  const links = document.querySelectorAll('#nav a');
  links.forEach(a => {
    if (a.getAttribute('href').endsWith(path)) {
      a.classList.add('current-page');
    }
  });
}

function setupSearch() {
  const box = document.getElementById('searchBox');
  box.addEventListener('input', () => {
    const q = box.value.toLowerCase();
    const links = document.querySelectorAll('#nav a');
    links.forEach(a => {
      const text = a.textContent.toLowerCase();
      a.style.display = text.includes(q) ? '' : 'none';
    });
  });
}

// ------------------------------
// 画像クリックで拡大表示（ダウンロード機能なし版）
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const viewer = document.getElementById("image-viewer");
  const viewerImg = document.getElementById("image-viewer-img");
  const closeBtn = document.getElementById("image-close");
  const zoomInBtn = document.getElementById("zoom-in");
  const zoomOutBtn = document.getElementById("zoom-out");

  let scale = 1;
  let imgX = 0;
  let imgY = 0;

  function updateTransform() {
    viewerImg.style.transform = `translate(${imgX}px, ${imgY}px) scale(${scale})`;
  }

  // Lightbox を開く
  document.querySelectorAll("#content img").forEach(img => {
    img.style.cursor = "zoom-in";
    img.addEventListener("click", () => {
      viewerImg.src = img.src;

      scale = 1;
      imgX = 0;
      imgY = 0;
      updateTransform();

      viewer.classList.remove("hidden");
      setTimeout(() => viewer.classList.add("show"), 10);
    });
  });

  // Lightbox を閉じる
  function closeViewer() {
    viewer.classList.remove("show");
    setTimeout(() => viewer.classList.add("hidden"), 200);
  }

  closeBtn.addEventListener("click", closeViewer);

  // 背景クリックで閉じる
  viewer.addEventListener("click", e => {
    if (e.target.id === "image-viewer") {
      closeViewer();
    }
  });

  // ホイールズーム
  viewerImg.addEventListener("wheel", e => {
    if (viewer.classList.contains("hidden")) return;

    e.preventDefault();
    scale += e.deltaY * -0.001;
    scale = Math.min(Math.max(0.1, scale), 10);
    updateTransform();
  });

  // ズームボタン
  zoomInBtn.addEventListener("click", () => {
    scale = Math.min(scale + 0.2, 10);
    updateTransform();
  });

  zoomOutBtn.addEventListener("click", () => {
    scale = Math.max(scale - 0.2, 0.1);
    updateTransform();
  });

  // ドラッグでパン
  let isDragging = false;
  let startX = 0;
  let startY = 0;

  viewerImg.addEventListener("mousedown", e => {
    isDragging = true;
    startX = e.clientX - imgX;
    startY = e.clientY - imgY;
    viewerImg.style.cursor = "grabbing";
  });

  document.addEventListener("mousemove", e => {
    if (!isDragging) return;
    imgX = e.clientX - startX;
    imgY = e.clientY - startY;
    updateTransform();
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    viewerImg.style.cursor = "zoom-out";
  });

  // キーボード操作
  document.addEventListener("keydown", e => {
    if (viewer.classList.contains("hidden")) return;

    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
      e.preventDefault();
    }

    if (e.key === "+") {
      scale = Math.min(scale + 0.2, 10);
      updateTransform();
    }

    if (e.key === "-") {
      scale = Math.max(scale - 0.2, 0.1);
      updateTransform();
    }

    if (e.key === "0") {
      scale = 1;
      imgX = 0;
      imgY = 0;
      updateTransform();
    }

    const move = 20;

    if (e.key === "ArrowLeft") {
      imgX += move;
      updateTransform();
    }

    if (e.key === "ArrowRight") {
      imgX -= move;
      updateTransform();
    }

    if (e.key === "ArrowUp") {
      imgY += move;
      updateTransform();
    }

    if (e.key === "ArrowDown") {
      imgY -= move;
      updateTransform();
    }

    if (e.key === "Escape") {
      closeViewer();
    }
  });

});
