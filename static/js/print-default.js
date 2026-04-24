window.addEventListener("load", () => {
    setTimeout(() => {
    loading.style.display = "none";
    window.print();
    }, 500);
});