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

  // すべての画像にクリックイベントを付与
  document.querySelectorAll("#content img").forEach(img => {
    img.style.cursor = "zoom-in";
    img.addEventListener("click", () => {
      viewerImg.src = img.src;
      viewer.classList.remove("hidden");
    });
  });

  // 閉じる
  closeBtn.addEventListener("click", () => {
    viewer.classList.add("hidden");
    viewerImg.style.transform = "scale(1)";
  });

  // 背景クリックでも閉じる
  viewer.addEventListener("click", (e) => {
    if (e.target === viewer) {
      viewer.classList.add("hidden");
      viewerImg.style.transform = "scale(1)";
    }
  });

  // ホイールズーム
  let scale = 1;
  viewerImg.addEventListener("wheel", (e) => {
    e.preventDefault();
    scale += e.deltaY * -0.001;
    scale = Math.min(Math.max(0.1, scale), 10);
    viewerImg.style.transform = `scale(${scale})`;
  });

  document.getElementById("zoom-in").addEventListener("click", () => {
    scale = Math.min(scale + 0.2, 5);
    viewerImg.style.transform = `scale(${scale})`;
  });

  document.getElementById("zoom-out").addEventListener("click", () => {
    scale = Math.max(scale - 0.2, 0.2);
    viewerImg.style.transform = `scale(${scale})`;
  });


  // ------------------------------
  // ドラッグで画像を移動（パン）
  // ------------------------------
  let isDragging = false;
  let startX = 0;
  let startY = 0;
  let imgX = 0;
  let imgY = 0;
  
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
    viewerImg.style.transform = `translate(${imgX}px, ${imgY}px) scale(${scale})`;
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
      scale = Math.min(scale + 0.2, 5);
      viewerImg.style.transform = `translate(${imgX}px, ${imgY}px) scale(${scale})`;
    }
  
    if (e.key === "-") {
      scale = Math.max(scale - 0.2, 0.2);
      viewerImg.style.transform = `translate(${imgX}px, ${imgY}px) scale(${scale})`;
    }
  
    if (e.key === "0") {
      scale = 1;
      imgX = 0;
      imgY = 0;
      viewerImg.style.transform = `scale(1)`;
    }
  
    if (e.key === "Escape") {
      viewer.classList.add("hidden");
      scale = 1;
      imgX = 0;
      imgY = 0;
      viewerImg.style.transform = "scale(1)";
    }
  });

});

