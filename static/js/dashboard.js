document.addEventListener("DOMContentLoaded", () => {
  // 1. Initial GSAP Animations
  if (typeof gsap !== "undefined") {
    gsap.from(".glass-nav", {
      y: -80,
      opacity: 0,
      duration: 1,
      ease: "power4.out",
    });
    gsap.from(".hero-section > *", {
      y: 30,
      opacity: 0,
      duration: 1,
      stagger: 0.15,
      ease: "power3.out",
      delay: 0.2,
    });
    gsap.from(".glass-card-anim", {
      y: 40,
      opacity: 0,
      duration: 0.8,
      stagger: 0.1,
      ease: "power3.out",
      delay: 0.5,
    });
  }

  // 2. Invite Modal Event Listeners
  const modal = document.getElementById("inviteModal");
  const btnOpenEmpty = document.getElementById("btn-open-invite-empty");
  const btnOpenGrid = document.getElementById("btn-open-invite-grid");
  const btnClose = document.getElementById("btn-close-invite");

  if (btnOpenEmpty) {
    btnOpenEmpty.addEventListener(
      "click",
      () => (modal.style.display = "flex"),
    );
  }

  if (btnOpenGrid) {
    btnOpenGrid.addEventListener("click", () => (modal.style.display = "flex"));
  }

  if (btnClose) {
    btnClose.addEventListener("click", () => (modal.style.display = "none"));
  }

  // Close modal if user clicks outside the content box
  window.addEventListener("click", (event) => {
    if (event.target === modal) {
      modal.style.display = "none";
    }
  });
});
