"""
EP020 후삼국과 고려 건국 - 이미지 프롬프트
대본 내용에 정확히 맞춘 이미지 생성용 프롬프트 (34장)
"""

# 섹션 1: 훅 - 세 영웅 소개 (3장)
SECTION_01_HOOK = [
    {
        "scene_index": 1,
        "description": "견훤이 완산주에서 왕을 선언",
        "prompt": "Traditional East Asian ink wash painting style, Gyeon Hwon declaring himself king in Wansan-ju 892 AD, strong military commander in armor raising sword, soldiers cheering, ancient Korean city gates, dramatic sunrise, brushstroke texture, muted earth tones"
    },
    {
        "scene_index": 2,
        "description": "한쪽 눈을 잃은 궁예",
        "prompt": "Traditional East Asian ink wash painting style, Gungye the one-eyed monk leading rebel forces, intense gaze from single eye, Buddhist robes with warrior armor, followers behind him, 9th century Korean military scene, dramatic lighting"
    },
    {
        "scene_index": 3,
        "description": "송악의 젊은 왕건",
        "prompt": "Traditional East Asian ink wash painting style, young Wang Geon in Songak (Kaesong), wealthy merchant family background, trading ships in harbor, confident young nobleman, 9th century Korean coastal town"
    },
]

# 섹션 2: 신라 하대의 혼란 (4장)
SECTION_02_SILLA_CHAOS = [
    {
        "scene_index": 4,
        "description": "혜공왕 시해 장면",
        "prompt": "Traditional East Asian ink wash painting style, assassination of King Hyegong of Silla 780 AD, palace coup scene, nobles with swords drawn, throne room in chaos, dramatic tension, Korean historical tragedy"
    },
    {
        "scene_index": 5,
        "description": "진골 귀족들의 왕위 쟁탈전",
        "prompt": "Traditional East Asian ink wash painting style, Silla noble factions fighting for throne, jingol aristocrats in conflict, royal court filled with intrigue, political chaos, 9th century Korean palace interior"
    },
    {
        "scene_index": 6,
        "description": "150년간 20명의 왕",
        "prompt": "Traditional East Asian ink wash painting style, symbolic image of many Silla kings passing quickly, multiple crowns and royal seals scattered, time passing rapidly, instability represented visually, abstract historical concept"
    },
    {
        "scene_index": 7,
        "description": "지방 통제력 상실",
        "prompt": "Traditional East Asian ink wash painting style, Silla capital losing control over provinces, messengers unable to collect taxes, distant regions ignoring central orders, fragmented kingdom map concept"
    },
]

# 섹션 3: 호족의 등장 (4장)
SECTION_03_HOJOK = [
    {
        "scene_index": 8,
        "description": "호족 요새",
        "prompt": "Traditional East Asian ink wash painting style, local strongman (hojok) fortress in mountains, private army training in courtyard, independent power base, 9th century Korean regional lord's stronghold"
    },
    {
        "scene_index": 9,
        "description": "호족이 군대를 기르는 장면",
        "prompt": "Traditional East Asian ink wash painting style, hojok leader inspecting his private troops, armed soldiers lined up, fortress walls in background, local military power, independent commander"
    },
    {
        "scene_index": 10,
        "description": "송악 왕씨 가문",
        "prompt": "Traditional East Asian ink wash painting style, Wang clan mansion in Songak, maritime trading wealth displayed, ships in harbor, prosperous merchant family, Wang Geon's childhood home"
    },
    {
        "scene_index": 11,
        "description": "해상 무역선",
        "prompt": "Traditional East Asian ink wash painting style, Korean trading ships sailing to Tang China, cargo of silk and goods, maritime commerce, 9th century East Asian sea trade routes"
    },
]

# 섹션 4: 견훤과 후백제 (4장)
SECTION_04_GYEONHWON = [
    {
        "scene_index": 12,
        "description": "군인 견훤의 젊은 시절",
        "prompt": "Traditional East Asian ink wash painting style, young Gyeon Hwon as military officer, coastal defense duty, watching ships from fortress, ambitious soldier's gaze, 9th century Korean military"
    },
    {
        "scene_index": 13,
        "description": "원종과 애노의 난",
        "prompt": "Traditional East Asian ink wash painting style, peasant rebellion 889 AD, farmers with improvised weapons rising up, burning tax collectors' offices, social unrest across Silla"
    },
    {
        "scene_index": 14,
        "description": "견훤이 무진주 장악",
        "prompt": "Traditional East Asian ink wash painting style, Gyeon Hwon capturing Mujin-ju (Gwangju), victorious commander entering city gates, local people watching, first major conquest"
    },
    {
        "scene_index": 15,
        "description": "후백제 건국 선언",
        "prompt": "Traditional East Asian ink wash painting style, Gyeon Hwon proclaiming Later Baekje 892 AD, king in ceremonial robes, Jeonju palace, reviving Baekje's legacy, dramatic declaration scene"
    },
]

# 섹션 5: 궁예의 등장 (5장)
SECTION_05_GUNGYE = [
    {
        "scene_index": 16,
        "description": "궁예의 비극적 탄생",
        "prompt": "Traditional East Asian ink wash painting style, baby being thrown from palace wall at night, nurse catching infant, mysterious light above, dark palace silhouette, tragic royal birth legend"
    },
    {
        "scene_index": 17,
        "description": "승려가 된 궁예",
        "prompt": "Traditional East Asian ink wash painting style, young Gungye as Buddhist monk at Sedal temple, shaved head, one eye covered, deep resentment hidden beneath calm exterior"
    },
    {
        "scene_index": 18,
        "description": "891년 도적 무리 합류",
        "prompt": "Traditional East Asian ink wash painting style, Gungye joining bandit group in Jukju, rebel camp in forest, outcasts and rebels gathered, new warrior emerging from monk"
    },
    {
        "scene_index": 19,
        "description": "궁예가 강릉 장악",
        "prompt": "Traditional East Asian ink wash painting style, Gungye conquering Myeongju (Gangneung) 894 AD, victorious rebel leader on horseback, coastal city falling under his control"
    },
    {
        "scene_index": 20,
        "description": "후고구려 건국",
        "prompt": "Traditional East Asian ink wash painting style, Gungye founding Later Goguryeo 901 AD, declaring himself king, Goguryeo revival banner raised, new kingdom born from rebellion"
    },
]

# 섹션 6: 왕건의 성장 (4장)
SECTION_06_WANGGEON = [
    {
        "scene_index": 21,
        "description": "왕건 가문이 궁예에게 귀순",
        "prompt": "Traditional East Asian ink wash painting style, Wang Ryung and young Wang Geon submitting to Gungye 896 AD, strategic alliance, Songak hojok joining powerful ruler"
    },
    {
        "scene_index": 22,
        "description": "왕건의 해상 전투",
        "prompt": "Traditional East Asian ink wash painting style, Wang Geon commanding naval fleet, Korean warships attacking enemy ports, brilliant naval strategist, sea battle scene"
    },
    {
        "scene_index": 23,
        "description": "나주 공략",
        "prompt": "Traditional East Asian ink wash painting style, Wang Geon's navy capturing Naju 903 AD, cutting off Later Baekje's rear, strategic maritime victory"
    },
    {
        "scene_index": 24,
        "description": "궁예 휘하의 명장",
        "prompt": "Traditional East Asian ink wash painting style, Wang Geon receiving honors from Gungye, trusted general rising in ranks, Taebong court scene"
    },
]

# 섹션 7: 궁예의 몰락과 고려 건국 (4장)
SECTION_07_GORYEO_FOUNDING = [
    {
        "scene_index": 25,
        "description": "태봉 궁궐의 궁예",
        "prompt": "Traditional East Asian ink wash painting style, King Gungye in Taebong palace at Cheorwon, claiming to be Maitreya Buddha, increasingly paranoid ruler, ominous atmosphere"
    },
    {
        "scene_index": 26,
        "description": "관심법으로 신하 처형",
        "prompt": "Traditional East Asian ink wash painting style, Gungye using gwansimbeop mind-reading to condemn officials, terrified courtiers, tyrannical judgment scene, fear spreading in court"
    },
    {
        "scene_index": 27,
        "description": "918년 쿠데타",
        "prompt": "Traditional East Asian ink wash painting style, four generals (Hong Yu, Bae Hyeon-gyeong, Sin Sung-gyeom, Bok Ji-gyeom) overthrowing Gungye 918 AD, palace coup, dramatic night scene"
    },
    {
        "scene_index": 28,
        "description": "왕건 즉위",
        "prompt": "Traditional East Asian ink wash painting style, Wang Geon crowned as first king of Goryeo 918 AD, new dynasty beginning, modest ceremony, hopeful atmosphere"
    },
]

# 섹션 8: 후삼국 전쟁 (3장)
SECTION_08_WAR = [
    {
        "scene_index": 29,
        "description": "경주 기습과 경애왕 시해",
        "prompt": "Traditional East Asian ink wash painting style, Gyeon Hwon's surprise attack on Gyeongju 927 AD, chaos in Silla capital, tragic death of King Gyeongae"
    },
    {
        "scene_index": 30,
        "description": "공산 전투",
        "prompt": "Traditional East Asian ink wash painting style, Battle of Gongsan (Palgongsan) 927 AD, Wang Geon's army surrounded, desperate fighting, Sin Sung-gyeom's sacrifice wearing king's armor"
    },
    {
        "scene_index": 31,
        "description": "고창 전투 승리",
        "prompt": "Traditional East Asian ink wash painting style, Battle of Gochang (Andong) 930 AD, Goryeo victory over Later Baekje, turning point of war, triumphant Goryeo army"
    },
]

# 섹션 9: 통일 완성 (3장)
SECTION_09_UNIFICATION = [
    {
        "scene_index": 32,
        "description": "견훤 망명",
        "prompt": "Traditional East Asian ink wash painting style, elderly Gyeon Hwon (70 years old) arriving at Goryeo as refugee 935 AD, betrayed by sons, Wang Geon welcoming former enemy respectfully"
    },
    {
        "scene_index": 33,
        "description": "신라 항복",
        "prompt": "Traditional East Asian ink wash painting style, King Gyeongsun of Silla surrendering to Goryeo 935 AD, end of thousand-year Silla dynasty, peaceful transfer of power"
    },
    {
        "scene_index": 34,
        "description": "일리천 전투와 통일",
        "prompt": "Traditional East Asian ink wash painting style, Battle of Illicheon 936 AD, massive Goryeo army defeating Later Baekje, final victory, Wang Geon triumphant, unified Korea"
    },
]

# 전체 프롬프트 합치기
ALL_PROMPTS = (
    SECTION_01_HOOK +
    SECTION_02_SILLA_CHAOS +
    SECTION_03_HOJOK +
    SECTION_04_GYEONHWON +
    SECTION_05_GUNGYE +
    SECTION_06_WANGGEON +
    SECTION_07_GORYEO_FOUNDING +
    SECTION_08_WAR +
    SECTION_09_UNIFICATION
)

def get_all_prompts():
    """전체 이미지 프롬프트 반환"""
    return ALL_PROMPTS
