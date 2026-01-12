"""
EP021 광종, 피의 개혁자 - 이미지 프롬프트
새 규칙 적용: 영상 길이 기반 동적 타이밍 (600자/분 기준)
- 0~1분: 10초마다 (6장)
- 1~5분: 30초마다 (8장)
- 5~10분: 40초마다 (8장)
- 10분~끝: 60초마다 (10장)
총 32장 (20분 영상 기준)
"""

# 이미지 프롬프트 - 타임스탬프 순서
IMAGE_PROMPTS = [
    # === 0~1분: 10초 간격 (훅 + 도입) - 6장 ===
    {
        "timestamp_sec": 0,
        "timestamp_display": "0:00",
        "description": "949년 광종 즉위",
        "prompt": "Korean webtoon style illustration, young King Gwangjong (25 years old) ascending throne of Goryeo 949 AD, solemn coronation ceremony, Kaesong palace, ministers bowing, dramatic lighting, 16:9"
    },
    {
        "timestamp_sec": 10,
        "timestamp_display": "0:10",
        "description": "혜종과 정종의 짧은 재위",
        "prompt": "Korean webtoon style illustration, two shadowy figures of previous Goryeo kings (Hyejong and Jeongjong), unstable throne, brief reigns symbolized, political turmoil atmosphere, 16:9"
    },
    {
        "timestamp_sec": 20,
        "timestamp_display": "0:20",
        "description": "왕위 쟁탈의 혼란",
        "prompt": "Korean webtoon style illustration, Goryeo princes and nobles fighting for power, palace intrigue, tense confrontation, early Goryeo period, dramatic shadows, 16:9"
    },
    {
        "timestamp_sec": 30,
        "timestamp_display": "0:30",
        "description": "피의 개혁자 광종",
        "prompt": "Korean webtoon style illustration, determined young King Gwangjong with fierce eyes, blood-red accents symbolizing future reforms, Goryeo royal robes, cinematic portrait, 16:9"
    },
    {
        "timestamp_sec": 40,
        "timestamp_display": "0:40",
        "description": "태조 왕건의 29명 부인",
        "prompt": "Korean webtoon style illustration, King Taejo Wang Geon surrounded by multiple wives from different hojok clans, marriage alliance politics visualized, Goryeo palace, 16:9"
    },
    {
        "timestamp_sec": 50,
        "timestamp_display": "0:50",
        "description": "25명의 왕자들",
        "prompt": "Korean webtoon style illustration, many princes of Goryeo from different mothers standing together, succession crisis brewing, each backed by different hojok clans, 16:9"
    },

    # === 1~5분: 30초 간격 (배경 설명) - 8장 ===
    {
        "timestamp_sec": 60,
        "timestamp_display": "1:00",
        "description": "혜종의 어머니 나주 오씨",
        "prompt": "Korean webtoon style illustration, Queen from Naju Oh clan with young Crown Prince Hyejong, weaker political backing, vulnerable position in Goryeo court, 16:9"
    },
    {
        "timestamp_sec": 90,
        "timestamp_display": "1:30",
        "description": "강력한 외가 - 충주 유씨와 황주 황보씨",
        "prompt": "Korean webtoon style illustration, powerful hojok clans of Chungju Yu and Hwangju Hwangbo displaying military and economic strength, rival factions, fortress backgrounds, 16:9"
    },
    {
        "timestamp_sec": 120,
        "timestamp_display": "2:00",
        "description": "왕규의 난",
        "prompt": "Korean webtoon style illustration, Wang Gyu's rebellion against King Hyejong 943 AD, conspiracy exposed, soldiers arresting traitor, palace coup scene, 16:9"
    },
    {
        "timestamp_sec": 150,
        "timestamp_display": "2:30",
        "description": "스트레스로 쓰러진 혜종",
        "prompt": "Korean webtoon style illustration, King Hyejong collapsing from stress and illness, only 2 years on throne, pale face, worried palace physicians, somber atmosphere, 16:9"
    },
    {
        "timestamp_sec": 180,
        "timestamp_display": "3:00",
        "description": "정종의 서경 천도 시도",
        "prompt": "Korean webtoon style illustration, King Jeongjong looking at map showing Kaesong and Seogyeong (Pyongyang), planning capital relocation, ministers debating, 16:9"
    },
    {
        "timestamp_sec": 210,
        "timestamp_display": "3:30",
        "description": "개경 호족들의 반대",
        "prompt": "Korean webtoon style illustration, Kaesong hojok nobles angrily opposing capital relocation plan, political resistance, heated court argument, 16:9"
    },
    {
        "timestamp_sec": 240,
        "timestamp_display": "4:00",
        "description": "호족들의 독립적 권력",
        "prompt": "Korean webtoon style illustration, regional hojok lords in their own fortresses, private armies training, semi-independent power bases across Goryeo territory, 16:9"
    },
    {
        "timestamp_sec": 270,
        "timestamp_display": "4:30",
        "description": "왕건의 훈요십조",
        "prompt": "Korean webtoon style illustration, Taejo's Ten Injunctions scroll being read, dying king's warnings about hojok power, serious atmosphere, candlelit scene, 16:9"
    },

    # === 5~10분: 40초 간격 (본론 - 개혁) - 8장 ===
    {
        "timestamp_sec": 300,
        "timestamp_display": "5:00",
        "description": "광종의 선택 - 강력한 왕권",
        "prompt": "Korean webtoon style illustration, young King Gwangjong making fateful decision, choosing strong kingship over compromise, determined expression, dramatic lighting, 16:9"
    },
    {
        "timestamp_sec": 340,
        "timestamp_display": "5:40",
        "description": "7년간 조용히 기다리는 광종",
        "prompt": "Korean webtoon style illustration, King Gwangjong sitting alone in contemplation, patient ruler observing court, chess-like strategic thinking, calm before storm, 16:9"
    },
    {
        "timestamp_sec": 380,
        "timestamp_display": "6:20",
        "description": "불교 후원으로 세력 구축",
        "prompt": "Korean webtoon style illustration, King Gwangjong patronizing Buddhist temples, building new temples, monks as alternative power base separate from hojok, 16:9"
    },
    {
        "timestamp_sec": 420,
        "timestamp_display": "7:00",
        "description": "956년 노비안검법 선포",
        "prompt": "Korean webtoon style illustration, King Gwangjong dramatically announcing Slave Review Act 956 AD, royal decree unfurling, shocked nobles, hopeful slaves, 16:9"
    },
    {
        "timestamp_sec": 460,
        "timestamp_display": "7:40",
        "description": "노비 조사 과정",
        "prompt": "Korean webtoon style illustration, royal officials investigating slave status, questioning people about origins, documents examined, liberation process beginning, 16:9"
    },
    {
        "timestamp_sec": 500,
        "timestamp_display": "8:20",
        "description": "양인 신분 회복",
        "prompt": "Korean webtoon style illustration, freed slaves receiving liberation documents, emotional reunions, grateful people bowing to king's portrait, hope and relief, warm tones, 16:9"
    },
    {
        "timestamp_sec": 540,
        "timestamp_display": "9:00",
        "description": "쌍기와 과거제도 제안",
        "prompt": "Korean webtoon style illustration, Chinese scholar Ssanggi from Later Zhou advising King Gwangjong, presenting civil examination system proposal 958 AD, scholarly discussion, 16:9"
    },
    {
        "timestamp_sec": 580,
        "timestamp_display": "9:40",
        "description": "958년 첫 과거시험",
        "prompt": "Korean webtoon style illustration, first civil service examination in Goryeo history, scholars writing with brushes, examination hall filled with candidates, historic moment, 16:9"
    },

    # === 10분~20분: 60초 간격 (클라이맥스 + 마무리) - 10장 ===
    {
        "timestamp_sec": 600,
        "timestamp_display": "10:00",
        "description": "과거 급제자들",
        "prompt": "Korean webtoon style illustration, successful examination candidates receiving appointments, new officials loyal to king not hojok, merit-based system established, 16:9"
    },
    {
        "timestamp_sec": 660,
        "timestamp_display": "11:00",
        "description": "숙청의 시작",
        "prompt": "Korean webtoon style illustration, Gwangjong's purge begins 960s, founding nobles being arrested for treason, soldiers dragging away ministers, dark atmosphere of fear, 16:9"
    },
    {
        "timestamp_sec": 720,
        "timestamp_display": "12:00",
        "description": "왕식렴 숙청",
        "prompt": "Korean webtoon style illustration, powerful Wang Singnyeom (Taejo's cousin and founding hero) being arrested, dramatic fall from grace, shocked onlookers, 16:9"
    },
    {
        "timestamp_sec": 780,
        "timestamp_display": "13:00",
        "description": "공포의 조정",
        "prompt": "Korean webtoon style illustration, terrified Goryeo court officials saying goodbye to families each morning, atmosphere of dread, empty seats in court, blood purge era, 16:9"
    },
    {
        "timestamp_sec": 840,
        "timestamp_display": "14:00",
        "description": "밀고와 처형",
        "prompt": "Korean webtoon style illustration, informants whispering accusations, mass arrests, prisons overflowing with accused nobles, reign of terror at its peak, 16:9"
    },
    {
        "timestamp_sec": 900,
        "timestamp_display": "15:00",
        "description": "독자 연호 광덕 선포",
        "prompt": "Korean webtoon style illustration, King Gwangjong declaring independent era name Gwangdeok 960 AD, asserting emperor-like authority, majestic throne room, imperial symbols, 16:9"
    },
    {
        "timestamp_sec": 960,
        "timestamp_display": "16:00",
        "description": "복식 제도 개편",
        "prompt": "Korean webtoon style illustration, new dress code being enforced, purple robes for high officials only, strict hierarchy in clothing colors, orderly court, 16:9"
    },
    {
        "timestamp_sec": 1020,
        "timestamp_display": "17:00",
        "description": "975년 광종 서거",
        "prompt": "Korean webtoon style illustration, death of King Gwangjong 975 AD after 26 years reign, elderly king on deathbed, end of an era, bittersweet atmosphere, 16:9"
    },
    {
        "timestamp_sec": 1080,
        "timestamp_display": "18:00",
        "description": "광종의 유산 - 중앙집권 국가",
        "prompt": "Korean webtoon style illustration, legacy of Gwangjong visualized, strong centralized Goryeo kingdom emerging, civil examination continuing, foundation for 500 years, 16:9"
    },
    {
        "timestamp_sec": 1140,
        "timestamp_display": "19:00",
        "description": "다음 예고 - 거란의 침략",
        "prompt": "Korean webtoon style illustration, ominous preview of Khitan (Liao) invasion threat, nomadic warriors on horseback approaching Korean peninsula, dramatic sunset, 16:9"
    },
]


def get_all_prompts():
    """전체 이미지 프롬프트 반환"""
    return IMAGE_PROMPTS


def get_prompt_by_timestamp(timestamp_sec: int):
    """특정 타임스탬프의 프롬프트 반환"""
    for prompt in IMAGE_PROMPTS:
        if prompt["timestamp_sec"] == timestamp_sec:
            return prompt
    return None


def get_prompt_count():
    """이미지 프롬프트 개수 반환"""
    return len(IMAGE_PROMPTS)
