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
// 画像クリックで拡大表示
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const viewer = document.getElementById("image-viewer");
  const viewerImg = document.getElementById("image-viewer-img");
  const closeBtn = document.getElementById("image-close");

  if (!viewer || !viewerImg || !closeBtn) {
    console.warn("Lightbox elements not found");
    return;
  }

  // ------------------------------
  // ズーム・パンの状態管理
  // ------------------------------
  let scale = 1;
  let imgX = 0;
  let imgY = 0;

  function updateTransform() {
    viewerImg.style.transform = `translate(${imgX}px, ${imgY}px) scale(${scale})`;
  }

  // ------------------------------
  // 画像クリックで Lightbox 表示
  // ------------------------------
  document.querySelectorAll("#content img").forEach(img => {
    img.style.cursor = "zoom-in";
    img.addEventListener("click", () => {
      viewerImg.src = img.src;
      scale = 1;
      imgX = 0;
      imgY = 0;
      updateTransform();
      viewer.classList.remove("hidden");
    });
  });

  // ------------------------------
  // 閉じる
  // ------------------------------
  closeBtn.addEventListener("click", () => {
    viewer.classList.add("hidden");
  });

  viewer.addEventListener("click", (e) => {
    if (e.target === viewer) {
      viewer.classList.add("hidden");
    }
  });

  // ------------------------------
  // ホイールズーム（Lightbox が開いている時だけ）
  // ------------------------------
  viewerImg.addEventListener("wheel", (e) => {
    if (viewer.classList.contains("hidden")) {
      // Lightbox が閉じている → ページの zoom に wheel を渡す
      return;
    }
  
    // Lightbox が開いている → wheel を Lightbox が奪う
    e.preventDefault();
    scale += e.deltaY * -0.001;
    scale = Math.min(Math.max(0.1, scale), 10);
    updateTransform();
  });

  // ------------------------------
  // ズームボタン
  // ------------------------------
  document.getElementById("zoom-in").addEventListener("click", () => {
    scale = Math.min(scale + 0.2, 10);
    updateTransform();
  });

  document.getElementById("zoom-out").addEventListener("click", () => {
    scale = Math.max(scale - 0.2, 0.1);
    updateTransform();
  });

  // ------------------------------
  // ドラッグでパン
  // ------------------------------
  let isDragging = false;
  let startX = 0;
  let startY = 0;

  viewerImg.addEventListener("mousedown", (e) => {
    isDragging = true;
    startX = e.clientX - imgX;
    startY = e.clientY - imgY;
    viewerImg.style.cursor = "grabbing";
  });

  document.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    imgX = e.clientX - startX;
    imgY = e.clientY - startY;
    updateTransform();
  });

  document.addEventListener("mouseup", () => {
    isDragging = false;
    viewerImg.style.cursor = "zoom-out";
  });

  // ------------------------------
  // キーボード操作
  // ------------------------------
  document.addEventListener("keydown", (e) => {
    if (viewer.classList.contains("hidden")) return;

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

    if (e.key === "Escape") {
      viewer.classList.add("hidden");
    }
  });

});
