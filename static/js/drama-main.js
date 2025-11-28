/**
 * Drama Lab - 메인 모듈
 * 초기화됨: 2024-11-28
 */

// ===== 전역 상태 =====
window.dramaApp = {
  currentStep: 1,
  session: null
};

// ===== 초기화 =====
document.addEventListener('DOMContentLoaded', () => {
  console.log('[DramaMain] 앱 초기화');
  initApp();
});

function initApp() {
  console.log('[DramaMain] Drama Lab 시작');
}
