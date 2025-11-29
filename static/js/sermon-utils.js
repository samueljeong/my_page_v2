/**
 * sermon-utils.js
 * 유틸리티 함수 모음 (의존성 없음)
 */

// ===== 한글 → 영문 ID 자동 생성 =====
function koreanToId(korean) {
  const map = {
    '제목': 'title',
    '아이스브래이킹': 'icebreaking',
    '서론': 'intro',
    '본론': 'body',
    '결론': 'conclusion',
    '본문': 'analysis',
    '분석': 'analysis',
    '신학': 'theology',
    '해석': 'interpretation',
    '예화': 'illustration',
    '적용': 'application',
    '실천': 'practice',
    '과제': 'task',
    '질문': 'questions',
    '토론': 'discussion',
    '기도': 'prayer',
    '개요': 'outline'
  };

  for (const [key, value] of Object.entries(map)) {
    if (korean.includes(key)) {
      return value + '_' + Date.now().toString(36);
    }
  }

  return 'step_' + Date.now().toString(36);
}

// 카테고리 ID 생성 함수 (category1, category2, ... 순차적)
function generateCategoryId() {
  let maxNum = 0;
  window.config.categories.forEach(cat => {
    const match = cat.value.match(/^category(\d+)$/);
    if (match) {
      const num = parseInt(match[1], 10);
      if (num > maxNum) maxNum = num;
    }
  });
  return 'category' + (maxNum + 1);
}

// ===== 상태 표시 =====
function showStatus(msg) {
  const statusBar = document.getElementById('status-bar');
  if (statusBar) {
    statusBar.textContent = msg;
    statusBar.style.display = 'block';
  }
}

function hideStatus() {
  const statusBar = document.getElementById('status-bar');
  if (statusBar) {
    statusBar.style.display = 'none';
  }
}

// ===== GPT 로딩 표시 =====
let currentLoadingMessage = '';

function showGptLoading(message, isStep3 = false) {
  currentLoadingMessage = message || '처리 중입니다...';
  const guideDiv = document.getElementById('start-analysis-guide');
  const startBtn = document.getElementById('btn-start-analysis');

  // 버튼 비활성화
  if (startBtn) startBtn.style.display = 'none';

  // Step3인 경우 전체 오버레이 표시
  if (isStep3) {
    showStep3Overlay();
  }

  // 안내문구에 진행상황 표시
  if (guideDiv) {
    guideDiv.style.display = 'block';
    guideDiv.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    guideDiv.style.border = 'none';
    guideDiv.innerHTML = `<span style="font-size: .95rem; font-weight: 700; color: white;">⏳ ${currentLoadingMessage}</span>`;
  }
}

function hideGptLoading() {
  currentLoadingMessage = '';

  // Step3 오버레이 제거
  hideStep3Overlay();

  // UI 상태 업데이트 (안내 문구도 updateAnalysisUI에서 처리)
  if (typeof updateAnalysisUI === 'function') {
    updateAnalysisUI();
  }
}

// Step3 전용 오버레이 표시
function showStep3Overlay() {
  // 기존 오버레이 제거
  hideStep3Overlay();

  const dualRow = document.querySelector('.dual-row');
  if (!dualRow) return;

  const overlay = document.createElement('div');
  overlay.className = 'step3-loading-overlay';
  overlay.innerHTML = `
    <div class="step3-loading-content">
      <div class="step3-loading-title">설교문 생성 중</div>
      <div class="step3-loading-subtitle">AI가 정성껏 설교문을 작성하고 있습니다</div>
      <div class="step3-loading-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;

  dualRow.appendChild(overlay);
}

// Step3 오버레이 제거
function hideStep3Overlay() {
  const overlay = document.querySelector('.step3-loading-overlay');
  if (overlay) {
    overlay.remove();
  }
}

function updateLoadingMessage(message) {
  currentLoadingMessage = message;
  const guideDiv = document.getElementById('start-analysis-guide');
  if (guideDiv && guideDiv.style.display !== 'none') {
    guideDiv.innerHTML = `<span style="font-size: .95rem; font-weight: 700; color: white;">⏳ ${message}</span>`;
  }
}

// ===== 모델별 가격 정보 (1M 토큰당 USD) =====
const modelPricing = {
  'gpt-4o-mini': { input: 0.15, output: 0.60 },
  'gpt-4o': { input: 2.50, output: 10.00 },
  'gpt-5': { input: 5.00, output: 20.00 },
  'gpt-5.1': { input: 7.50, output: 30.00 }
};

// 비용 계산 함수 (원화, 소수점 1자리)
function calculateCost(modelId, inputTokens, outputTokens) {
  const pricing = modelPricing[modelId];
  if (!pricing) return null;
  const inputCost = (inputTokens / 1000000) * pricing.input;
  const outputCost = (outputTokens / 1000000) * pricing.output;
  const totalUSD = inputCost + outputCost;
  const totalKRW = (totalUSD * 1400).toFixed(1); // 원화 환산, 소수점 1자리
  return {
    inputCost: inputCost.toFixed(6),
    outputCost: outputCost.toFixed(6),
    totalCost: totalUSD.toFixed(6),
    totalCostKRW: totalKRW
  };
}

// ===== textarea 자동 크기 조절 =====
function autoResize(el) {
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = el.scrollHeight + 'px';
}

function autoResizeTextarea(textarea) {
  if (!textarea) return;
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
}

// ===== 헬퍼 함수 =====
function getCategoryLabel(value) {
  const cat = window.config.categories.find(c => c.value === value);
  return cat ? cat.label : value;
}

function getCurrentStyle() {
  const settings = window.config.categorySettings[window.currentCategory];
  return settings?.styles?.find(s => s.id === window.currentStyleId);
}

function getCurrentSteps() {
  const style = getCurrentStyle();
  return style?.steps || [];
}

function getStepName(stepId) {
  const steps = getCurrentSteps();
  const step = steps.find(s => s.id === stepId);
  return step ? step.name : stepId;
}

// ===== HTML 이스케이프 =====
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ===== 결과 텍스트 자르기 =====
function truncateResult(text, stepType = 'step2') {
  if (!text) return '';

  // step1은 200자, step2는 150자로 자르기
  const maxLength = stepType === 'step1' ? 200 : 150;

  // JSON인 경우 파싱 시도
  if (text.trim().startsWith('{')) {
    try {
      const parsed = JSON.parse(text);
      // JSON을 보기 좋게 포맷팅하고 자르기
      const formatted = JSON.stringify(parsed, null, 2);
      if (formatted.length > maxLength) {
        return formatted.substring(0, maxLength) + '...\n\n(더보기를 클릭하세요)';
      }
      return formatted;
    } catch (e) {
      // JSON 파싱 실패시 원본 텍스트 사용
    }
  }

  if (text.length > maxLength) {
    return text.substring(0, maxLength) + '...\n\n(더보기를 클릭하세요)';
  }
  return text;
}

function truncateToIntro(text) {
  if (!text) return '';
  const maxLength = 200;
  if (text.length > maxLength) {
    return text.substring(0, maxLength) + '...';
  }
  return text;
}

// 전역 노출
window.koreanToId = koreanToId;
window.generateCategoryId = generateCategoryId;
window.showStatus = showStatus;
window.hideStatus = hideStatus;
window.showGptLoading = showGptLoading;
window.hideGptLoading = hideGptLoading;
window.showStep3Overlay = showStep3Overlay;
window.hideStep3Overlay = hideStep3Overlay;
window.updateLoadingMessage = updateLoadingMessage;
window.modelPricing = modelPricing;
window.calculateCost = calculateCost;
window.autoResize = autoResize;
window.autoResizeTextarea = autoResizeTextarea;
window.getCategoryLabel = getCategoryLabel;
window.getCurrentStyle = getCurrentStyle;
window.getCurrentSteps = getCurrentSteps;
window.getStepName = getStepName;
window.escapeHtml = escapeHtml;
window.truncateResult = truncateResult;
window.truncateToIntro = truncateToIntro;
