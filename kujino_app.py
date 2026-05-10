"""
KUJINO - 개인용 쿠지 뽑기 소프트웨어
PyQt5 기반, 100장 카드 + 상품 관리 + 당첨 결과 + 쿠지판 수리 기능
"""

import sys
import os
import json
import random
import shutil
import math
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QScrollArea, QFrame, QLineEdit,
    QGraphicsOpacityEffect, QMessageBox, QInputDialog, QDialog, QFormLayout,
    QListWidget, QListWidgetItem, QFileDialog, QProgressBar, QSizePolicy,
    QDialogButtonBox, QSpinBox, QCheckBox
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize, pyqtProperty,
    QRect, QPoint, QPointF, pyqtSignal
)
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QFont, QPen, QBrush, QPixmap,
    QRadialGradient, QPainterPath, QPolygon, QIcon, QPainterPathStroker
)

# 사운드 라이브러리 (pygame). 선택적 임포트 - 없어도 앱은 동작
try:
    # pygame 시작 시 메시지 숨기기
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    import pygame
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except Exception as e:
    print(f"[알림] 사운드 비활성화: {e}")
    SOUND_AVAILABLE = False

# =============================================================================
# 경로 / 데이터 파일
# =============================================================================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_DIR, "kujino_data.json")
IMAGES_DIR = os.path.join(APP_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


def resource_path(rel):
    """PyInstaller --onefile로 빌드된 EXE에서도 리소스 파일 찾기"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 빌드된 경우 임시 폴더에서 찾음
        return os.path.join(sys._MEIPASS, rel)
    return os.path.join(APP_DIR, rel)


LOGO_PATH = resource_path(os.path.join("assets", "logo.png"))
LOGO_SMALL_PATH = resource_path(os.path.join("assets", "logo_small.png"))
SOUNDS_DIR = resource_path("sounds")
SESSIONS_DIR = os.path.join(APP_DIR, "sessions")
# 사운드/세션 폴더 자동 생성 (개발 모드일 때만)
if not hasattr(sys, '_MEIPASS'):
    os.makedirs(os.path.join(APP_DIR, "sounds"), exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)


# 카드 수와 상품 수 제한
MIN_CARDS = 6
MAX_CARDS = 100
MIN_PRIZES = 5
MAX_PRIZES = 99
DEFAULT_TOTAL_CARDS = 100
DEFAULT_PRIZE_COUNT = 5


# =============================================================================
# 사운드 매니저
# =============================================================================
class SoundManager:
    """카지노풍 효과음 재생 시스템.

    sounds/ 폴더에 다음 파일들을 넣으면 자동 재생:
      - bgm.mp3        : 배경 음악 (반복 재생)
      - suspense.mp3   : 뽑기 전 긴장감 (카드 오픈 직전)
      - flip.mp3       : 카드 뒤집기 효과음
      - win.mp3        : 당첨 팡파레
      - lose.mp3       : 꽝 사운드
      - click.mp3      : 카드 선택 (선택)
      - shuffle.mp3    : 섞기 (선택)

    파일이 없으면 그냥 조용히 넘어감 (앱은 정상 동작).
    """

    SOUND_FILES = {
        "bgm": "bgm",
        "suspense": "suspense",
        "flip": "flip",
        "win": "win",
        "lose": "lose",
        "click": "click",
        "shuffle": "shuffle",
    }
    EXTENSIONS = [".mp3", ".wav", ".ogg"]

    def __init__(self):
        self.sounds = {}
        self.bgm_playing = False
        self.enabled = SOUND_AVAILABLE
        self.volume = 0.7
        self.bgm_volume = 0.3
        if self.enabled:
            self._load_all()

    def _find_file(self, base_name):
        """확장자 무관하게 파일 찾기"""
        for ext in self.EXTENSIONS:
            path = os.path.join(SOUNDS_DIR, base_name + ext)
            if os.path.exists(path):
                return path
        return None

    def _load_all(self):
        """sounds 폴더에서 효과음 로드 (BGM 제외)"""
        for key, name in self.SOUND_FILES.items():
            if key == "bgm":
                continue  # BGM은 mixer.music으로 따로 처리
            path = self._find_file(name)
            if path:
                try:
                    self.sounds[key] = pygame.mixer.Sound(path)
                    self.sounds[key].set_volume(self.volume)
                    print(f"[사운드] {key} 로드됨: {os.path.basename(path)}")
                except Exception as e:
                    print(f"[사운드] {key} 로드 실패: {e}")

    def play(self, key):
        """효과음 한 번 재생"""
        if not self.enabled:
            return
        sound = self.sounds.get(key)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def play_bgm(self):
        """배경 음악 시작 (반복 재생)"""
        if not self.enabled or self.bgm_playing:
            return
        path = self._find_file("bgm")
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.bgm_volume)
            pygame.mixer.music.play(loops=-1)  # 무한 반복
            self.bgm_playing = True
            print(f"[사운드] BGM 재생 시작: {os.path.basename(path)}")
        except Exception as e:
            print(f"[사운드] BGM 재생 실패: {e}")

    def stop_bgm(self):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
            self.bgm_playing = False
        except Exception:
            pass

    def toggle_bgm(self):
        if self.bgm_playing:
            self.stop_bgm()
        else:
            self.play_bgm()
        return self.bgm_playing

    def set_muted(self, muted):
        """전체 음소거 토글"""
        if not self.enabled:
            return
        if muted:
            for s in self.sounds.values():
                s.set_volume(0)
            pygame.mixer.music.set_volume(0)
        else:
            for s in self.sounds.values():
                s.set_volume(self.volume)
            pygame.mixer.music.set_volume(self.bgm_volume)


# 전역 사운드 매니저
SOUND = SoundManager()

# 색상 팔레트 (KUJINO 테마)
COLOR_BG = "#0d0a06"
COLOR_PANEL = "#1a1308"
COLOR_BORDER = "#5C4A1F"
COLOR_GOLD = "#E8C547"
COLOR_GOLD_DARK = "#8B6F2D"
COLOR_GOLD_LIGHT = "#FFD970"
COLOR_TEXT = "#EFE5C5"
COLOR_TEXT_DIM = "#9A8C6E"
COLOR_RED = "#C73E3A"
COLOR_GREEN = "#3D9970"
COLOR_BLUE = "#3A7BD5"
COLOR_PURPLE = "#7B5FBE"


# =============================================================================
# 데이터 매니저: JSON 영속성 + 동적 카드/상품 수 지원
# =============================================================================
class DataManager:
    """모든 상태를 JSON 파일에 저장하고 로드.

    카드 수(total_cards)와 상품 수(prize_count)는 동적으로 변경 가능.
    제약: MIN_CARDS ≤ total_cards ≤ MAX_CARDS
          MIN_PRIZES ≤ prize_count ≤ MAX_PRIZES
          prize_count ≤ total_cards (강제)
    """

    def __init__(self):
        self.data = self._load_or_init()

    # -------------------------------------------------------------------------
    # 헬퍼 (편의 접근자)
    # -------------------------------------------------------------------------
    def total_cards(self):
        return self.data.get("total_cards", DEFAULT_TOTAL_CARDS)

    def prize_count(self):
        return len(self.data.get("prizes", []))

    # -------------------------------------------------------------------------
    # 로드 / 초기화
    # -------------------------------------------------------------------------
    def _load_or_init(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._ensure_keys(data)
                return data
            except Exception as e:
                print(f"데이터 로드 실패, 초기화: {e}")
        return self._fresh()

    def _fresh(self):
        prizes = []
        for i in range(DEFAULT_PRIZE_COUNT):
            prizes.append({"number": i + 1,
                          "name": self._default_prize_name(i + 1),
                          "image": ""})
        data = {
            "title": "쿠지노 자체쿠지",
            "subtitle": "KUJINO 뽑기 한판",
            "price_account": 15000,
            "price_store": 16000,
            "bank": "국민은행 000000-00-000000 홍길동",
            "total_cards": DEFAULT_TOTAL_CARDS,
            "prizes": prizes,
            "cards": [],  # 아래 _init_cards에서 채움
        }
        data["cards"] = self._make_cards(DEFAULT_TOTAL_CARDS, DEFAULT_PRIZE_COUNT)
        return data

    @staticmethod
    def _default_prize_name(n):
        """기본 상품 이름 자동 생성"""
        grade_map = {1: "S", 2: "A", 3: "B", 4: "C", 5: "D", 6: "E", 7: "F"}
        if n in grade_map:
            return f"{grade_map[n]}상 ({n}등)"
        return f"{n}등 상품"

    def _make_cards(self, total_cards, prize_count):
        """카드 목록 새로 생성: 1~prize_count번에는 상품, 나머지는 꽝(0).
        prize_number는 무작위로 섞어서 분포시킴."""
        prize_numbers = list(range(1, prize_count + 1)) + \
                        [0] * (total_cards - prize_count)
        random.shuffle(prize_numbers)
        cards = []
        for n in range(1, total_cards + 1):
            cards.append({
                "number": n,
                "prize_number": prize_numbers[n - 1],
                "opened": False,
            })
        return cards

    def _ensure_keys(self, data):
        """이전 버전 데이터 마이그레이션"""
        defaults = self._fresh()
        for k, v in defaults.items():
            if k not in data:
                data[k] = v
        # total_cards 키 보강
        if "total_cards" not in data:
            data["total_cards"] = len(data.get("cards", []))
        # 카드 수 일치 확인
        if len(data["cards"]) != data["total_cards"]:
            data["cards"] = self._make_cards(data["total_cards"], len(data["prizes"]))

    def save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 카드 / 상품 수 동적 변경
    # -------------------------------------------------------------------------
    def reconfigure(self, new_total_cards, new_prize_count):
        """카드 수와 상품 수를 변경하고 풀을 재구성.

        진행 중이던 게임은 초기화됨 (모든 카드 미오픈 상태로).
        반환값: (성공 여부, 메시지)
        """
        # 검증
        new_total_cards = max(MIN_CARDS, min(MAX_CARDS, new_total_cards))
        new_prize_count = max(MIN_PRIZES, min(MAX_PRIZES, new_prize_count))
        if new_prize_count > new_total_cards:
            return False, f"상품 개수({new_prize_count})는 카드 수({new_total_cards})보다 많을 수 없습니다."

        # 상품 목록 조정
        current_prizes = self.data["prizes"]
        if new_prize_count > len(current_prizes):
            # 추가
            for i in range(len(current_prizes), new_prize_count):
                current_prizes.append({
                    "number": i + 1,
                    "name": self._default_prize_name(i + 1),
                    "image": "",
                })
        elif new_prize_count < len(current_prizes):
            # 삭제 (뒤에서부터)
            self.data["prizes"] = current_prizes[:new_prize_count]

        # 카드 풀 재생성 (진행 중인 게임 리셋)
        self.data["total_cards"] = new_total_cards
        self.data["cards"] = self._make_cards(new_total_cards, new_prize_count)
        return True, f"카드 {new_total_cards}장, 상품 {new_prize_count}개로 변경되었습니다."

    # -------------------------------------------------------------------------
    # 상품 / 카드 헬퍼
    # -------------------------------------------------------------------------
    def find_prize(self, prize_number):
        if prize_number <= 0:
            return None
        for p in self.data["prizes"]:
            if p["number"] == prize_number:
                return p
        return None

    def shuffle_unopened(self):
        """아직 열리지 않은 카드들끼리만 prize_number를 섞음"""
        unopened = [c for c in self.data["cards"] if not c["opened"]]
        prize_numbers = [c["prize_number"] for c in unopened]
        random.shuffle(prize_numbers)
        for c, pn in zip(unopened, prize_numbers):
            c["prize_number"] = pn

    def reset_all(self):
        """모든 카드 미오픈 + 다시 섞기 (수와 상품 그대로)"""
        self.data["cards"] = self._make_cards(self.total_cards(), self.prize_count())

    def stats(self):
        opened = sum(1 for c in self.data["cards"] if c["opened"])
        total = len(self.data["cards"])
        remaining = total - opened
        percent = int(opened / total * 100) if total else 0
        return {"total": total, "opened": opened, "remaining": remaining, "percent": percent}

    def prize_remaining(self, prize_number):
        for c in self.data["cards"]:
            if c["prize_number"] == prize_number and not c["opened"]:
                return 1
        return 0

    def winners(self):
        result = []
        for c in self.data["cards"]:
            if c["opened"] and c["prize_number"] > 0:
                prize = self.find_prize(c["prize_number"])
                if prize:
                    result.append({"number": c["number"], "prize": prize})
        return result

    def all_drawn(self):
        result = []
        for c in self.data["cards"]:
            if c["opened"]:
                result.append({
                    "number": c["number"],
                    "prize_number": c["prize_number"],
                    "prize_name": self.find_prize(c["prize_number"])["name"]
                                   if c["prize_number"] > 0 else "꽝(랜덤굿즈)"
                })
        return result

    # -------------------------------------------------------------------------
    # 세션 저장 / 불러오기 (이름 붙은 여러 세션)
    # -------------------------------------------------------------------------
    def list_sessions(self):
        """sessions/ 폴더의 저장된 세션 목록 반환."""
        try:
            files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
            sessions = []
            for f in files:
                path = os.path.join(SESSIONS_DIR, f)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        d = json.load(fp)
                    stats = self._stats_for_data(d)
                    sessions.append({
                        "name": f[:-5],
                        "title": d.get("title", "(이름 없음)"),
                        "total": stats["total"],
                        "opened": stats["opened"],
                        "percent": stats["percent"],
                        "modified": os.path.getmtime(path),
                    })
                except Exception as e:
                    print(f"세션 {f} 읽기 실패: {e}")
            sessions.sort(key=lambda s: s["modified"], reverse=True)
            return sessions
        except Exception as e:
            print(f"세션 목록 실패: {e}")
            return []

    @staticmethod
    def _stats_for_data(d):
        cards = d.get("cards", [])
        opened = sum(1 for c in cards if c.get("opened"))
        total = len(cards)
        percent = int(opened / total * 100) if total else 0
        return {"total": total, "opened": opened, "percent": percent}

    def save_as_session(self, name):
        """현재 상태를 이름 붙여 별도 파일로 저장"""
        # 파일명 안전 처리
        safe = "".join(c for c in name if c.isalnum() or c in " _-가-힣ㄱ-ㅎㅏ-ㅣ").strip()
        if not safe:
            safe = "untitled"
        path = os.path.join(SESSIONS_DIR, f"{safe}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True, path
        except Exception as e:
            return False, str(e)

    def load_session(self, name):
        """저장된 세션 불러오기"""
        path = os.path.join(SESSIONS_DIR, f"{name}.json")
        if not os.path.exists(path):
            return False, "파일을 찾을 수 없습니다."
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._ensure_keys(data)
            self.data = data
            self.save()  # 메인 파일에도 반영
            return True, "불러오기 완료"
        except Exception as e:
            return False, str(e)

    def delete_session(self, name):
        path = os.path.join(SESSIONS_DIR, f"{name}.json")
        try:
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception:
            return False

    def export_to_file(self, filepath):
        """현재 상태를 임의 경로로 내보내기 (백업)"""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True, "내보내기 완료"
        except Exception as e:
            return False, str(e)

    def import_from_file(self, filepath):
        """파일에서 상태 가져오기 (백업 복원)"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._ensure_keys(data)
            self.data = data
            self.save()
            return True, "가져오기 완료"
        except Exception as e:
            return False, str(e)


# =============================================================================
# 반짝거림 파티클 효과 (화면 전체 오버레이)
# =============================================================================
class Particle:
    """단일 파티클 (별, 점, 동전 등)"""
    __slots__ = ('x', 'y', 'vx', 'vy', 'gravity', 'life', 'max_life',
                 'size', 'color', 'shape', 'rotation', 'spin')

    def __init__(self, x, y, vx, vy, color, shape="star", size=8,
                 life=60, gravity=0.15):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.gravity = gravity
        self.life = life
        self.max_life = life
        self.size = size
        self.color = color
        self.shape = shape
        self.rotation = random.uniform(0, 360)
        self.spin = random.uniform(-12, 12)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.99  # 약간의 공기저항
        self.rotation += self.spin
        self.life -= 1

    def alpha(self):
        """남은 수명에 따른 투명도 (0~1)"""
        if self.life <= 0:
            return 0
        # 끝 30%에서 페이드아웃
        fade_start = self.max_life * 0.3
        if self.life > fade_start:
            return 1.0
        return self.life / fade_start


class SparkleOverlay(QWidget):
    """화면 위에 떠있는 투명 레이어. 파티클 효과를 그림."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 마우스 이벤트 통과시키기 (아래 버튼 클릭 가능)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        # 투명 배경
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.setInterval(16)  # 약 60 FPS

        # 콘페티/별 색상 팔레트
        self.gold_palette = [
            QColor("#FFD700"),
            QColor("#FFC107"),
            QColor("#FFEB3B"),
            QColor("#FFAB00"),
            QColor("#FF6F00"),
            QColor("#FFFFFF"),
        ]
        self.colorful_palette = [
            QColor("#FF1744"), QColor("#FFD700"), QColor("#00E676"),
            QColor("#00B0FF"), QColor("#D500F9"), QColor("#FF6F00"),
            QColor("#FFFFFF"), QColor("#FF80AB"),
        ]

    def _tick(self):
        # 모든 파티클 업데이트, 죽은 것 제거
        alive = []
        for p in self.particles:
            p.update()
            if p.life > 0 and p.y < self.height() + 50:
                alive.append(p)
        self.particles = alive
        if not self.particles:
            self.timer.stop()
        self.update()

    def burst(self, x, y, count=40, palette="gold", strength=12, shape="star"):
        """지정 위치에서 파티클 폭발"""
        colors = self.gold_palette if palette == "gold" else self.colorful_palette
        for _ in range(count):
            # 사방으로 퍼지는 각도
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(strength * 0.3, strength)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(2, 5)  # 위로 살짝 더
            color = random.choice(colors)
            size = random.randint(5, 12)
            life = random.randint(40, 90)
            p = Particle(x, y, vx, vy, color, shape=shape,
                         size=size, life=life, gravity=0.18)
            self.particles.append(p)
        if not self.timer.isActive():
            self.timer.start()

    def confetti_rain(self, count=80):
        """화면 상단에서 콘페티 비처럼 떨어뜨림"""
        w = self.width()
        for _ in range(count):
            x = random.uniform(0, w)
            y = random.uniform(-100, -10)
            vx = random.uniform(-2, 2)
            vy = random.uniform(2, 5)
            color = random.choice(self.colorful_palette)
            size = random.randint(6, 12)
            life = random.randint(120, 200)
            p = Particle(x, y, vx, vy, color, shape="confetti",
                         size=size, life=life, gravity=0.08)
            self.particles.append(p)
        if not self.timer.isActive():
            self.timer.start()

    def sparkle_around(self, rect, count=20):
        """사각형 영역 주변에 반짝이는 별 뿌리기"""
        for _ in range(count):
            x = random.uniform(rect.left(), rect.right())
            y = random.uniform(rect.top(), rect.bottom())
            vx = random.uniform(-1, 1)
            vy = random.uniform(-3, -1)
            color = random.choice(self.gold_palette)
            size = random.randint(4, 8)
            life = random.randint(30, 60)
            p = Particle(x, y, vx, vy, color, shape="sparkle",
                         size=size, life=life, gravity=0.05)
            self.particles.append(p)
        if not self.timer.isActive():
            self.timer.start()

    def clear(self):
        self.particles.clear()
        self.timer.stop()
        self.update()

    def paintEvent(self, ev):
        if not self.particles:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for particle in self.particles:
            self._draw_particle(p, particle)

    def _draw_particle(self, painter, particle):
        alpha = int(particle.alpha() * 255)
        if alpha <= 0:
            return
        color = QColor(particle.color)
        color.setAlpha(alpha)

        painter.save()
        painter.translate(particle.x, particle.y)
        painter.rotate(particle.rotation)

        if particle.shape == "star":
            self._draw_star(painter, particle.size, color)
        elif particle.shape == "sparkle":
            self._draw_sparkle(painter, particle.size, color)
        elif particle.shape == "confetti":
            self._draw_confetti(painter, particle.size, color)
        elif particle.shape == "coin":
            self._draw_coin(painter, particle.size, color)
        else:
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(0, 0), particle.size, particle.size)

        painter.restore()

    def _draw_star(self, p, r, color):
        """5각 별"""
        path = QPainterPath()
        for i in range(10):
            angle = i * math.pi / 5 - math.pi / 2
            radius = r if i % 2 == 0 else r * 0.4
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        p.setBrush(QBrush(color))
        # 빛나는 효과를 위한 외곽선
        glow = QColor(color)
        glow.setAlpha(min(255, color.alpha() + 30))
        p.setPen(QPen(glow, 1))
        p.drawPath(path)

    def _draw_sparkle(self, p, r, color):
        """+ 모양 반짝이"""
        p.setPen(QPen(color, 2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-r, 0), QPointF(r, 0))
        p.drawLine(QPointF(0, -r), QPointF(0, r))
        # 작은 대각선
        r2 = r * 0.5
        p.setPen(QPen(color, 1, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-r2, -r2), QPointF(r2, r2))
        p.drawLine(QPointF(-r2, r2), QPointF(r2, -r2))

    def _draw_confetti(self, p, r, color):
        """직사각형 콘페티"""
        p.setBrush(QBrush(color))
        p.setPen(Qt.NoPen)
        p.drawRect(QRect(int(-r / 2), int(-r / 4), r, r // 2))

    def _draw_coin(self, p, r, color):
        """동전 모양"""
        grad = QRadialGradient(0, 0, r)
        grad.setColorAt(0, color.lighter(140))
        grad.setColorAt(0.7, color)
        grad.setColorAt(1, color.darker(150))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(color.darker(200), 1))
        p.drawEllipse(QPointF(0, 0), r, r)


# =============================================================================
# 카드 위젯 (방패 모양 + 로고 / 뒤집어진 후엔 번호와 결과)
# =============================================================================
class ShieldCard(QPushButton):
    """방패 모양으로 그려지는 카드 위젯"""

    # 클래스 변수: 로고 이미지 한 번만 로드하여 재사용
    _logo_pixmap = None

    @classmethod
    def get_logo(cls):
        if cls._logo_pixmap is None:
            if os.path.exists(LOGO_SMALL_PATH):
                pix = QPixmap(LOGO_SMALL_PATH)
                if not pix.isNull():
                    cls._logo_pixmap = pix.scaled(
                        46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
        return cls._logo_pixmap

    def __init__(self, number, parent=None):
        super().__init__(parent)
        self.number = number
        self.is_opened = False
        self.is_selected = False
        self.is_winner = False  # 상품 당첨 여부 (열렸을 때만 의미)
        self._flip = 0.0
        self._pulse = 0.0  # 0~1 두근거림 (선택 시 빛남 강도)
        self._pulse_dir = 1
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._tick_pulse)
        self.pulse_timer.setInterval(40)
        self.setFixedSize(82, 100)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet("background: transparent; border: none;")

    def _tick_pulse(self):
        self._pulse += 0.06 * self._pulse_dir
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_dir = 1
        self.update()

    def get_flip(self):
        return self._flip

    def set_flip(self, v):
        self._flip = v
        self.update()

    flip = pyqtProperty(float, get_flip, set_flip)

    def open_card(self, is_winner=False):
        self.is_opened = True
        self.is_winner = is_winner
        self.is_selected = False
        anim = QPropertyAnimation(self, b"flip", self)
        anim.setDuration(600)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._anim = anim  # 참조 유지

    def reset(self):
        self.is_opened = False
        self.is_selected = False
        self.is_winner = False
        self._flip = 0.0
        self.update()

    def set_selected(self, sel):
        self.is_selected = sel
        if sel:
            self._pulse = 0.0
            self._pulse_dir = 1
            self.pulse_timer.start()
        else:
            self.pulse_timer.stop()
            self._pulse = 0.0
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(3, 3, -3, -3)

        # 뒤집기 효과 (가로 스케일)
        scale = abs(1 - 2 * self._flip)
        if scale < 0.05:
            scale = 0.05
        p.translate(rect.center())
        p.scale(scale, 1.0)
        p.translate(-rect.center())

        # 방패 모양 path
        path = self._shield_path(rect)

        if self._flip < 0.5:
            self._draw_back(p, rect, path)
        else:
            self._draw_front(p, rect, path)

    def _shield_path(self, rect):
        """방패(역오각형 비슷) 모양 만들기"""
        path = QPainterPath()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        # 위쪽: 둥근 사각형, 아래쪽: 뾰족
        top_h = h * 0.72
        path.moveTo(x + 8, y)
        path.lineTo(x + w - 8, y)
        # 오른쪽 위 모서리
        path.quadTo(x + w, y, x + w, y + 8)
        path.lineTo(x + w, y + top_h)
        # 오른쪽 아래 곡선 → 뾰족 끝
        path.quadTo(x + w, y + top_h + 10, x + w / 2, y + h)
        path.quadTo(x, y + top_h + 10, x, y + top_h)
        path.lineTo(x, y + 8)
        path.quadTo(x, y, x + 8, y)
        path.closeSubpath()
        return path

    def _draw_back(self, p, rect, path):
        """뒷면: 미공개 (로고 보임)"""
        # 그림자
        if not self.is_opened:
            shadow_path = QPainterPath(path)
            p.fillPath(shadow_path.translated(0, 2), QColor(0, 0, 0, 100))

        # 본체: 갈색 + 황금 그라데이션
        if self.is_opened:
            # 어둡게 (뒷면 잠깐 보일 때)
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, QColor("#2a2218"))
            grad.setColorAt(1, QColor("#15110a"))
        else:
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, QColor("#3d2d18"))
            grad.setColorAt(0.5, QColor("#2d2010"))
            grad.setColorAt(1, QColor("#1a1208"))
        p.fillPath(path, QBrush(grad))

        # 외곽선 (선택 시 황금 + 펄스 후광)
        if self.is_selected:
            # 후광 효과: 펄스 강도에 따라 점점 진해지는 외곽선 여러 겹
            for i in range(4, 0, -1):
                glow_alpha = int(80 * self._pulse * (5 - i) / 4)
                glow_color = QColor(COLOR_GOLD_LIGHT)
                glow_color.setAlpha(glow_alpha)
                p.setPen(QPen(glow_color, i * 2))
                p.drawPath(path)
            # 메인 외곽선
            pen_color = QColor(COLOR_GOLD_LIGHT)
            pen_width = 3
        else:
            pen_color = QColor(COLOR_GOLD_DARK)
            pen_width = 1.5
        p.setPen(QPen(pen_color, pen_width))
        p.drawPath(path)

        # 중앙 KUJINO 로고 (이미지)
        if not self.is_opened:
            logo = self.get_logo()
            if logo:
                # 카드 중앙에 배치 (번호 영역 위)
                lw, lh = logo.width(), logo.height()
                lx = rect.center().x() - lw // 2
                ly = rect.y() + int(rect.height() * 0.62 - lh) // 2 + 4
                p.drawPixmap(lx, ly, logo)
            else:
                # 폴백: 직접 그리기
                cx, cy = rect.center().x(), rect.center().y() - 6
                radial = QRadialGradient(cx, cy, 18)
                radial.setColorAt(0, QColor("#FFD970"))
                radial.setColorAt(0.6, QColor("#C9A227"))
                radial.setColorAt(1, QColor("#5C4A1F"))
                p.setBrush(QBrush(radial))
                p.setPen(QPen(QColor("#3a2a10"), 1.5))
                p.drawEllipse(cx - 15, cy - 15, 30, 30)
                p.setPen(QColor("#2a1a05"))
                f = QFont("Georgia", 13, QFont.Black)
                p.setFont(f)
                p.drawText(QRect(cx - 15, cy - 15, 30, 30), Qt.AlignCenter, "K")

        # 번호 (하단)
        p.setPen(QColor(COLOR_GOLD if not self.is_opened else "#444"))
        f = QFont("Arial", 10, QFont.Bold)
        p.setFont(f)
        # 번호는 방패 위쪽 평평한 영역의 아래쪽에
        num_rect = QRect(rect.x(), rect.y() + int(rect.height() * 0.62),
                         rect.width(), 20)
        p.drawText(num_rect, Qt.AlignCenter, f"{self.number:03d}")

    def _draw_front(self, p, rect, path):
        """앞면: 열린 후 모습"""
        if self.is_winner:
            # 당첨: 황금색
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, QColor("#FFE48A"))
            grad.setColorAt(0.5, QColor(COLOR_GOLD))
            grad.setColorAt(1, QColor("#A88420"))
            p.fillPath(path, QBrush(grad))
            p.setPen(QPen(QColor("#5a4510"), 2.5))
            p.drawPath(path)

            # WIN 표시
            p.setPen(QColor("#3a2a05"))
            f = QFont("Georgia", 18, QFont.Black)
            p.setFont(f)
            p.drawText(rect.adjusted(0, -8, 0, -10), Qt.AlignCenter, "★")

            p.setPen(QColor("#3a2a05"))
            f = QFont("Arial", 8, QFont.Bold)
            p.setFont(f)
            p.drawText(rect.adjusted(0, 8, 0, 0), Qt.AlignCenter, "WIN")
        else:
            # 꽝: 어둡게
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0, QColor("#2a2520"))
            grad.setColorAt(1, QColor("#15120e"))
            p.fillPath(path, QBrush(grad))
            p.setPen(QPen(QColor("#3a3025"), 1.5))
            p.drawPath(path)

            # 꽝 표시
            p.setPen(QColor("#5a4a30"))
            f = QFont("Arial", 10, QFont.Bold)
            p.setFont(f)
            p.drawText(rect.adjusted(0, -10, 0, -10), Qt.AlignCenter, "꽝")
            p.setPen(QColor("#3a3025"))
            f = QFont("Arial", 7)
            p.setFont(f)
            p.drawText(rect.adjusted(0, 8, 0, 0), Qt.AlignCenter, "랜덤굿즈")

        # 번호
        p.setPen(QColor("#2a1f05") if self.is_winner else QColor("#5a4a30"))
        f = QFont("Arial", 9, QFont.Bold)
        p.setFont(f)
        num_rect = QRect(rect.x(), rect.y() + int(rect.height() * 0.62),
                         rect.width(), 20)
        p.drawText(num_rect, Qt.AlignCenter, f"{self.number:03d}")


# =============================================================================
# KUJINO 로고 위젯 (좌측 상단) - 이미지 파일 기반
# =============================================================================
class KujinoLogo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setMinimumWidth(200)
        self.setFixedWidth(200)
        # 로고 이미지 로드
        self.logo_pixmap = None
        if os.path.exists(LOGO_PATH):
            pix = QPixmap(LOGO_PATH)
            if not pix.isNull():
                # 60x60 크기로 부드럽게 리사이즈
                self.logo_pixmap = pix.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        rect = self.rect()

        # 배경 (테두리)
        p.setPen(QPen(QColor(COLOR_GOLD_DARK), 1.5))
        p.setBrush(QBrush(QColor("#0a0805")))
        p.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)

        # 로고 이미지 (왼쪽)
        emblem_size = 60
        ex = rect.x() + 5
        ey = rect.y() + (rect.height() - emblem_size) // 2

        if self.logo_pixmap:
            p.drawPixmap(ex, ey, self.logo_pixmap)
        else:
            # 이미지 없을 때 폴백: 황금 원
            p.setBrush(QBrush(QColor(COLOR_GOLD)))
            p.setPen(QPen(QColor("#3a2a10"), 1.5))
            p.drawEllipse(ex, ey, emblem_size, emblem_size)
            p.setPen(QColor("#2a1a05"))
            f = QFont("Georgia", 20, QFont.Black)
            p.setFont(f)
            p.drawText(QRect(ex, ey, emblem_size, emblem_size), Qt.AlignCenter, "K")

        # 텍스트 영역
        text_x = ex + emblem_size + 12

        # ===== 한글: "쿠 지 노" - 균일 간격 =====
        # 각 글자마다 같은 폭의 칸을 정해놓고 중앙 정렬해서 그림
        korean_chars = ["쿠", "지", "노"]
        char_box_w = 32  # 글자 한 칸 폭
        char_y = rect.y() + 8
        char_h = 32

        p.setPen(QColor(COLOR_GOLD_LIGHT))
        f_kor = QFont("Malgun Gothic", 19, QFont.Black)
        p.setFont(f_kor)
        for i, ch in enumerate(korean_chars):
            cell = QRect(text_x + i * char_box_w, char_y, char_box_w, char_h)
            p.drawText(cell, Qt.AlignCenter, ch)

        # ===== 영문: "K U J I N O" - 한글 전체 폭에 균등 분배 =====
        # 한글 3글자 전체 폭 = char_box_w * 3
        total_w = char_box_w * 3
        eng_chars = list("KUJINO")
        eng_box_w = total_w / len(eng_chars)
        eng_y = rect.y() + 44
        eng_h = 18

        p.setPen(QColor(COLOR_GOLD_DARK))
        f_eng = QFont("Arial", 10, QFont.Bold)
        p.setFont(f_eng)
        for i, ch in enumerate(eng_chars):
            cell = QRect(int(text_x + i * eng_box_w), eng_y,
                         int(eng_box_w), eng_h)
            p.drawText(cell, Qt.AlignCenter, ch)


# =============================================================================
# 진행률 바 (전체 N장 / 남은 / 오픈 / 퍼센트)
# =============================================================================
class ProgressPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.text_label = QLabel()
        self.text_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; background: transparent;")
        layout.addWidget(self.text_label)

        # 커스텀 진행바
        self.bar = QFrame()
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet(f"""
            QFrame {{
                background: #15110a;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        bar_layout = QHBoxLayout(self.bar)
        bar_layout.setContentsMargins(1, 1, 1, 1)
        bar_layout.setSpacing(0)

        self.fill = QFrame()
        self.fill.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLOR_GOLD_DARK}, stop:1 {COLOR_GOLD_LIGHT});
                border-radius: 3px;
            }}
        """)
        bar_layout.addWidget(self.fill)
        self.spacer = QFrame()
        self.spacer.setStyleSheet("background: transparent;")
        bar_layout.addWidget(self.spacer)

        layout.addWidget(self.bar)

    def update_stats(self, stats):
        self.text_label.setText(
            f"전체 {stats['total']}장   ·   남은 {stats['remaining']}장   ·   "
            f"오픈 {stats['opened']}장        {stats['percent']}%"
        )
        # 비율 적용
        total_w = max(1, self.bar.width() - 2)
        fill_w = int(total_w * stats['percent'] / 100)
        self.fill.setFixedWidth(fill_w if fill_w > 0 else 0)
        self.spacer.setFixedWidth(total_w - fill_w)


# =============================================================================
# 가격/계좌 정보 패널 (3개 박스)
# =============================================================================
class InfoBoxes(QWidget):
    edit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.box_account = self._make_box(COLOR_GOLD, "계좌 장당", "")
        self.box_store = self._make_box(COLOR_GREEN, "스토어 장당", "")
        self.box_bank = self._make_box(COLOR_BLUE, "입금계좌", "")

        layout.addWidget(self.box_account)
        layout.addWidget(self.box_store)
        layout.addWidget(self.box_bank, stretch=2)

    def _make_box(self, accent_color, label_text, value_text):
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{
                background: #1a1308;
                border: 1.5px solid {accent_color};
                border-radius: 8px;
            }}
        """)
        box.setCursor(Qt.PointingHandCursor)
        box.mousePressEvent = lambda e: self.edit_requested.emit()

        v = QVBoxLayout(box)
        v.setContentsMargins(10, 6, 10, 6)
        v.setSpacing(2)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {accent_color}; font-size: 10px; font-weight: bold; background: transparent; border: none;")
        v.addWidget(lbl)

        val = QLabel(value_text)
        val.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        v.addWidget(val)

        box.value_label = val
        return box

    def update_values(self, price_account, price_store, bank):
        self.box_account.value_label.setText(f"{price_account:,}원")
        self.box_store.value_label.setText(f"{price_store:,}원")
        self.box_bank.value_label.setText(bank)


# =============================================================================
# 남은 상품 카드 (오른쪽 패널의 각 항목)
# =============================================================================
class PrizeCard(QFrame):
    def __init__(self, prize, remaining=1, parent=None):
        super().__init__(parent)
        self.prize = prize
        self.remaining = remaining
        self.setMinimumHeight(180)
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: #1a1308;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(4)

        # 헤더 (이름 + 잔여)
        header = QHBoxLayout()
        # 상태 점
        dot = QLabel("●")
        if self.remaining > 0:
            dot.setStyleSheet("color: #4DD0E1; font-size: 12px; background: transparent; border: none;")
        else:
            dot.setStyleSheet("color: #555; font-size: 12px; background: transparent; border: none;")
        header.addWidget(dot)

        name = QLabel(self.prize["name"])
        name.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        header.addWidget(name)
        header.addStretch()

        rem_lbl = QLabel(f"{self.remaining}/1")
        if self.remaining > 0:
            rem_lbl.setStyleSheet(f"color: #4DD0E1; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        else:
            rem_lbl.setStyleSheet(f"color: #555; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        header.addWidget(rem_lbl)
        v.addLayout(header)

        # 이미지
        img_label = QLabel()
        img_label.setMinimumHeight(120)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet(f"background: #0a0805; border-radius: 4px; border: none;")

        if self.prize.get("image") and os.path.exists(self.prize["image"]):
            pix = QPixmap(self.prize["image"])
            if not pix.isNull():
                pix = pix.scaled(220, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                if self.remaining == 0:
                    # 어둡게: 픽스맵 위에 검은 반투명 덮어씌움
                    dark = QPixmap(pix.size())
                    dark.fill(Qt.transparent)
                    p = QPainter(dark)
                    p.drawPixmap(0, 0, pix)
                    p.fillRect(dark.rect(), QColor(0, 0, 0, 160))
                    # X 표시
                    p.setPen(QPen(QColor(200, 60, 60, 220), 4))
                    p.drawLine(10, 10, dark.width() - 10, dark.height() - 10)
                    p.drawLine(dark.width() - 10, 10, 10, dark.height() - 10)
                    p.end()
                    pix = dark
                img_label.setPixmap(pix)
            else:
                img_label.setText("[이미지 로드 실패]")
                img_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; background: #0a0805; border-radius: 4px; border: none;")
        else:
            img_label.setText("이미지 없음\n(쿠지판 수리에서 추가)")
            img_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 10px; background: #0a0805; border-radius: 4px; border: none;")

        v.addWidget(img_label)


# =============================================================================
# 쿠지판 수리 다이얼로그 (상품 추가/수정/삭제 + 가격/계좌 편집)
# =============================================================================
class RepairDialog(QDialog):
    def __init__(self, dm: DataManager, parent=None):
        super().__init__(parent)
        self.dm = dm
        self.setWindowTitle("쿠지판 수리하기")
        self.setMinimumSize(560, 720)
        self.setStyleSheet(f"""
            QDialog {{ background: {COLOR_BG}; color: {COLOR_TEXT}; }}
            QLabel {{ color: {COLOR_TEXT}; }}
            QLineEdit, QSpinBox {{
                background: {COLOR_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton {{
                background: {COLOR_PANEL};
                color: {COLOR_GOLD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #2a2010; }}
            QListWidget {{
                background: {COLOR_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QListWidget::item:selected {{ background: {COLOR_GOLD_DARK}; color: black; }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # ==== 기본 정보 ====
        meta_box = QFrame()
        meta_box.setStyleSheet(f"QFrame {{ background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}")
        form = QFormLayout(meta_box)
        form.setContentsMargins(15, 12, 15, 12)
        form.setSpacing(6)

        self.title_edit = QLineEdit(self.dm.data["title"])
        form.addRow("쿠지 이름:", self.title_edit)

        self.subtitle_edit = QLineEdit(self.dm.data.get("subtitle", ""))
        form.addRow("부제목:", self.subtitle_edit)

        self.price_account_edit = QSpinBox()
        self.price_account_edit.setRange(0, 9999999)
        self.price_account_edit.setValue(self.dm.data["price_account"])
        self.price_account_edit.setSuffix(" 원")
        form.addRow("계좌 장당:", self.price_account_edit)

        self.price_store_edit = QSpinBox()
        self.price_store_edit.setRange(0, 9999999)
        self.price_store_edit.setValue(self.dm.data["price_store"])
        self.price_store_edit.setSuffix(" 원")
        form.addRow("스토어 장당:", self.price_store_edit)

        self.bank_edit = QLineEdit(self.dm.data["bank"])
        form.addRow("입금계좌:", self.bank_edit)

        layout.addWidget(meta_box)

        # ==== 카드 / 상품 수 조정 ====
        config_label = QLabel("◆ 카드 수 / 상품 개수")
        config_label.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 13px; font-weight: bold;")
        layout.addWidget(config_label)

        config_box = QFrame()
        config_box.setStyleSheet(f"QFrame {{ background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 6px; }}")
        config_form = QFormLayout(config_box)
        config_form.setContentsMargins(15, 12, 15, 12)
        config_form.setSpacing(6)

        self.total_cards_edit = QSpinBox()
        self.total_cards_edit.setRange(MIN_CARDS, MAX_CARDS)
        self.total_cards_edit.setValue(self.dm.total_cards())
        self.total_cards_edit.setSuffix(" 장")
        self.total_cards_edit.valueChanged.connect(self._sync_constraints)
        config_form.addRow(f"카드 수 ({MIN_CARDS}~{MAX_CARDS}):", self.total_cards_edit)

        self.prize_count_edit = QSpinBox()
        self.prize_count_edit.setRange(MIN_PRIZES, MAX_PRIZES)
        self.prize_count_edit.setValue(self.dm.prize_count())
        self.prize_count_edit.setSuffix(" 개")
        self.prize_count_edit.valueChanged.connect(self._sync_constraints)
        config_form.addRow(f"상품 개수 ({MIN_PRIZES}~{MAX_PRIZES}):", self.prize_count_edit)

        warn_label = QLabel("⚠ 카드 수/상품 수를 변경하면 진행 중인 게임이 초기화됩니다.")
        warn_label.setStyleSheet(f"color: {COLOR_RED}; font-size: 11px; padding: 4px;")
        warn_label.setWordWrap(True)
        config_form.addRow(warn_label)

        layout.addWidget(config_box)

        # ==== 상품 목록 ====
        prize_label = QLabel("◆ 상품 목록 (1번부터 카드에 순서대로 매핑)")
        prize_label.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 13px; font-weight: bold;")
        layout.addWidget(prize_label)

        self.prize_list = QListWidget()
        self.prize_list.setMaximumHeight(180)
        self.prize_list.itemDoubleClicked.connect(self.edit_prize)
        self._refresh_prize_list()
        layout.addWidget(self.prize_list, stretch=1)

        # 상품 버튼
        btn_row = QHBoxLayout()
        edit_btn = QPushButton("✎  선택 상품 수정")
        edit_btn.clicked.connect(self.edit_selected)
        btn_row.addWidget(edit_btn)

        img_btn = QPushButton("🖼  이미지 변경")
        img_btn.clicked.connect(self.change_image)
        btn_row.addWidget(img_btn)
        layout.addLayout(btn_row)

        # 하단 OK/취소
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.save_and_close)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def _sync_constraints(self):
        """상품 수가 카드 수보다 많아지지 않도록 자동 조정"""
        cards = self.total_cards_edit.value()
        prizes = self.prize_count_edit.value()
        # 상품 수의 최댓값을 카드 수로 제한 (단, MAX_PRIZES 한도 내)
        max_p = min(MAX_PRIZES, cards)
        if self.prize_count_edit.maximum() != max_p:
            self.prize_count_edit.setMaximum(max_p)
        if prizes > cards:
            self.prize_count_edit.setValue(cards)

    def _refresh_prize_list(self):
        self.prize_list.clear()
        for prize in self.dm.data["prizes"]:
            img_status = "🖼" if prize.get("image") and os.path.exists(prize["image"]) else "□"
            item = QListWidgetItem(f"  {prize['number']}번  {img_status}   {prize['name']}")
            item.setData(Qt.UserRole, prize["number"])
            self.prize_list.addItem(item)

    def _selected_prize(self):
        item = self.prize_list.currentItem()
        if not item:
            QMessageBox.warning(self, "안내", "상품을 먼저 선택하세요.")
            return None
        num = item.data(Qt.UserRole)
        for p in self.dm.data["prizes"]:
            if p["number"] == num:
                return p
        return None

    def edit_selected(self):
        prize = self._selected_prize()
        if prize:
            self._edit_prize(prize)

    def edit_prize(self, item):
        num = item.data(Qt.UserRole)
        for p in self.dm.data["prizes"]:
            if p["number"] == num:
                self._edit_prize(p)
                break

    def _edit_prize(self, prize):
        text, ok = QInputDialog.getText(
            self, f"{prize['number']}번 상품 이름",
            "상품 이름:", QLineEdit.Normal, prize["name"]
        )
        if ok and text.strip():
            prize["name"] = text.strip()
            self._refresh_prize_list()

    def change_image(self):
        prize = self._selected_prize()
        if not prize:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, f"{prize['number']}번 상품 이미지 선택", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )
        if not path:
            return
        # 이미지를 images/ 폴더로 복사 (포터블)
        ext = os.path.splitext(path)[1].lower()
        dest = os.path.join(IMAGES_DIR, f"prize_{prize['number']}{ext}")
        try:
            shutil.copy2(path, dest)
            prize["image"] = dest
            self._refresh_prize_list()
            QMessageBox.information(self, "완료", f"이미지가 저장되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"이미지 복사 실패: {e}")

    def save_and_close(self):
        # 카드 수 / 상품 수가 변경되었는지 확인
        new_total = self.total_cards_edit.value()
        new_prize_count = self.prize_count_edit.value()
        old_total = self.dm.total_cards()
        old_prize_count = self.dm.prize_count()

        config_changed = (new_total != old_total or new_prize_count != old_prize_count)

        if config_changed:
            # 진행 중인 게임이 있는지 확인
            opened = sum(1 for c in self.dm.data["cards"] if c["opened"])
            if opened > 0:
                reply = QMessageBox.question(
                    self, "확인",
                    f"카드 수 또는 상품 수를 변경하면\n"
                    f"진행 중인 게임({opened}장 오픈됨)이 초기화됩니다.\n\n"
                    f"  • 카드: {old_total}장 → {new_total}장\n"
                    f"  • 상품: {old_prize_count}개 → {new_prize_count}개\n\n"
                    f"진행하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return  # 다이얼로그 닫지 않고 그대로

        # 메타 정보 저장
        self.dm.data["title"] = self.title_edit.text().strip() or "쿠지노 자체쿠지"
        self.dm.data["subtitle"] = self.subtitle_edit.text().strip()
        self.dm.data["price_account"] = self.price_account_edit.value()
        self.dm.data["price_store"] = self.price_store_edit.value()
        self.dm.data["bank"] = self.bank_edit.text().strip()

        # 카드/상품 수 변경 적용
        if config_changed:
            ok, msg = self.dm.reconfigure(new_total, new_prize_count)
            if not ok:
                QMessageBox.warning(self, "오류", msg)
                return

        self.dm.save()
        self.accept()


# =============================================================================
# 세션 관리 다이얼로그 (저장/불러오기/삭제)
# =============================================================================
class SessionManagerDialog(QDialog):
    """저장된 세션 목록을 보여주고 저장/불러오기/삭제하는 다이얼로그"""

    SAVE_MODE = "save"
    LOAD_MODE = "load"

    def __init__(self, dm: DataManager, mode="load", parent=None):
        super().__init__(parent)
        self.dm = dm
        self.mode = mode
        self.selected_session = None  # 선택된 세션 이름
        self.action_taken = None  # 'load' / 'save' / 'export' / 'import' / None

        title = "세션 불러오기" if mode == self.LOAD_MODE else "세션 저장"
        self.setWindowTitle(title)
        self.setMinimumSize(620, 500)
        self.setStyleSheet(f"""
            QDialog {{ background: {COLOR_BG}; color: {COLOR_TEXT}; }}
            QLabel {{ color: {COLOR_TEXT}; }}
            QLineEdit {{
                background: {COLOR_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton {{
                background: {COLOR_PANEL};
                color: {COLOR_GOLD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 8px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #2a2010; }}
            QListWidget {{
                background: {COLOR_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid #2a1f10;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QListWidget::item:selected {{ background: {COLOR_GOLD_DARK}; color: black; }}
        """)
        self._build()
        self._refresh_list()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 헤더
        header = QLabel("📚  저장된 쿠지 세션" if self.mode == self.LOAD_MODE
                        else "💾  현재 진행 상태 저장")
        header.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        # 안내문
        if self.mode == self.LOAD_MODE:
            info = QLabel("불러올 세션을 선택하세요. 현재 진행 상황은 사라집니다.")
        else:
            info = QLabel("이름을 입력하고 저장하세요. 같은 이름이면 덮어씁니다.")
        info.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # 저장 모드: 이름 입력
        if self.mode == self.SAVE_MODE:
            name_row = QHBoxLayout()
            name_row.addWidget(QLabel("세션 이름:"))
            # 기본값: 쿠지 제목 + 날짜
            from datetime import datetime
            default_name = f"{self.dm.data['title']}_{datetime.now().strftime('%m%d_%H%M')}"
            self.name_edit = QLineEdit(default_name)
            self.name_edit.returnPressed.connect(self._save_session)
            name_row.addWidget(self.name_edit, stretch=1)
            save_btn = QPushButton("💾  저장")
            save_btn.clicked.connect(self._save_session)
            name_row.addWidget(save_btn)
            layout.addLayout(name_row)

        # 세션 목록
        list_label = QLabel("📋  기존 세션 목록")
        list_label.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 13px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(list_label)

        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.session_list, stretch=1)

        # 액션 버튼들
        action_row = QHBoxLayout()
        if self.mode == self.LOAD_MODE:
            load_btn = QPushButton("📂 불러오기")
            load_btn.clicked.connect(self._load_session)
            action_row.addWidget(load_btn)

        del_btn = QPushButton("🗑 삭제")
        del_btn.clicked.connect(self._delete_session)
        action_row.addWidget(del_btn)

        action_row.addStretch()

        # 백업 (파일 내보내기/가져오기)
        export_btn = QPushButton("📤 내보내기")
        export_btn.setToolTip("백업 파일로 저장")
        export_btn.clicked.connect(self._export_to_file)
        action_row.addWidget(export_btn)

        if self.mode == self.LOAD_MODE:
            import_btn = QPushButton("📥 가져오기")
            import_btn.setToolTip("백업 파일에서 불러오기")
            import_btn.clicked.connect(self._import_from_file)
            action_row.addWidget(import_btn)
        layout.addLayout(action_row)

        # 닫기
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def _refresh_list(self):
        self.session_list.clear()
        sessions = self.dm.list_sessions()
        if not sessions:
            item = QListWidgetItem("  (저장된 세션이 없습니다)")
            item.setForeground(QColor(COLOR_TEXT_DIM))
            item.setFlags(Qt.NoItemFlags)
            self.session_list.addItem(item)
            return
        from datetime import datetime
        for s in sessions:
            mtime = datetime.fromtimestamp(s["modified"]).strftime("%Y-%m-%d %H:%M")
            text = (f"  {s['name']}\n"
                    f"     쿠지: {s['title']}  ·  진행: {s['opened']}/{s['total']} ({s['percent']}%)  ·  {mtime}")
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, s["name"])
            self.session_list.addItem(item)

    def _selected_name(self):
        item = self.session_list.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def _on_double_click(self, item):
        name = item.data(Qt.UserRole)
        if not name:
            return
        if self.mode == self.LOAD_MODE:
            self._load_session()

    def _save_session(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "안내", "세션 이름을 입력하세요.")
            return
        # 중복 확인
        sessions = self.dm.list_sessions()
        if any(s["name"] == name for s in sessions):
            reply = QMessageBox.question(
                self, "확인",
                f"'{name}' 세션이 이미 있습니다. 덮어쓰시겠습니까?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        ok, msg = self.dm.save_as_session(name)
        if ok:
            QMessageBox.information(self, "완료", f"'{name}'으로 저장되었습니다.")
            self.action_taken = "save"
            self._refresh_list()
        else:
            QMessageBox.critical(self, "오류", f"저장 실패: {msg}")

    def _load_session(self):
        name = self._selected_name()
        if not name:
            QMessageBox.warning(self, "안내", "불러올 세션을 선택하세요.")
            return
        reply = QMessageBox.question(
            self, "확인",
            f"'{name}' 세션을 불러옵니다.\n현재 진행 상황은 사라집니다.\n진행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        ok, msg = self.dm.load_session(name)
        if ok:
            self.action_taken = "load"
            self.accept()
        else:
            QMessageBox.critical(self, "오류", f"불러오기 실패: {msg}")

    def _delete_session(self):
        name = self._selected_name()
        if not name:
            QMessageBox.warning(self, "안내", "삭제할 세션을 선택하세요.")
            return
        reply = QMessageBox.question(
            self, "확인",
            f"'{name}' 세션을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        if self.dm.delete_session(name):
            self._refresh_list()

    def _export_to_file(self):
        from datetime import datetime
        default_name = f"kujino_백업_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "백업 파일 저장", default_name, "JSON 파일 (*.json)"
        )
        if not path:
            return
        ok, msg = self.dm.export_to_file(path)
        if ok:
            QMessageBox.information(self, "완료", f"백업 파일이 저장되었습니다:\n{path}")
        else:
            QMessageBox.critical(self, "오류", f"내보내기 실패: {msg}")

    def _import_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "백업 파일 선택", "", "JSON 파일 (*.json)"
        )
        if not path:
            return
        reply = QMessageBox.question(
            self, "확인",
            f"이 파일을 불러옵니다:\n{path}\n\n현재 진행 상황은 사라집니다. 진행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        ok, msg = self.dm.import_from_file(path)
        if ok:
            self.action_taken = "import"
            self.accept()
        else:
            QMessageBox.critical(self, "오류", f"가져오기 실패: {msg}")


# =============================================================================
# 긴장감 팝업 (카드 뒤집기 전, 룰렛처럼 숫자 돌아가는 효과)
# =============================================================================
class SuspensePopup(QDialog):
    """뽑기 직전 화려한 룰렛 효과로 긴장감 조성.
    완료되면 finished_signal로 알려줌."""

    finished_signal = pyqtSignal()

    def __init__(self, target_number, max_card=100, parent=None):
        super().__init__(parent)
        self.target = target_number
        self.max_card = max_card
        self.current_display = random.randint(1, max_card)
        self.start_time = time.monotonic()
        self.duration_sec = 2.2
        self._glow_phase = 0.0
        self._finished = False

        self.setFixedSize(460, 360)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        self._fade_in()

        # 룰렛 타이머 (점점 느려짐)
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._tick)
        self.tick_timer.start(50)

        # 펄스 애니메이션 타이머
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._tick_glow)
        self.glow_timer.start(40)

        # 사운드
        SOUND.play("suspense")

    def _build(self):
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, 460, 360)
        self.container.setStyleSheet(f"""
            QFrame {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.8,
                    stop:0 #1a1308, stop:1 #0a0805);
                border: 3px solid {COLOR_GOLD};
                border-radius: 16px;
            }}
        """)

        v = QVBoxLayout(self.container)
        v.setContentsMargins(30, 25, 30, 25)
        v.setSpacing(8)

        # 상단 안내
        self.top_label = QLabel("🎰  운명의 카드  🎰")
        self.top_label.setAlignment(Qt.AlignCenter)
        self.top_label.setStyleSheet(f"""
            color: {COLOR_GOLD_LIGHT};
            font-size: 20px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        v.addWidget(self.top_label)

        # 부제목
        self.sub_label = QLabel("두구두구두구...")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM};
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        v.addWidget(self.sub_label)

        # 큰 숫자 표시 영역 (커스텀 페인트할 거라 라벨로 두지만 paintEvent에서 그림)
        self.number_widget = NumberRoulette(self)
        v.addWidget(self.number_widget, stretch=1)

        # 하단 안내
        bottom = QLabel(f"카드 #{self.target:03d}")
        bottom.setAlignment(Qt.AlignCenter)
        bottom.setStyleSheet(f"color: {COLOR_GOLD_DARK}; font-size: 11px; background: transparent; border: none;")
        v.addWidget(bottom)

    def _tick(self):
        """룰렛 진행: 시간이 지날수록 숫자 변경 속도 느려지다가 target에 멈춤"""
        if self._finished:
            return
        elapsed = time.monotonic() - self.start_time
        progress = elapsed / self.duration_sec

        if progress >= 1.0:
            self._finished = True
            self.current_display = self.target
            self.number_widget.set_number(self.current_display, final=True)
            self.tick_timer.stop()
            # 1초 뒤에 닫고 결과 팝업으로
            QTimer.singleShot(800, self._finish)
            return

        # 진행에 따라 갱신 간격 늘어남 (가속도 곡선)
        new_interval = int(50 + progress * progress * 250)
        self.tick_timer.setInterval(new_interval)

        # 끝에 가까워지면 target 주변 숫자만 보여줌
        if progress > 0.85:
            self.current_display = self.target + random.randint(-3, 3)
            self.current_display = max(1, min(self.max_card, self.current_display))
        else:
            self.current_display = random.randint(1, self.max_card)

        self.number_widget.set_number(self.current_display)

        # tick 사운드
        if progress < 0.9:
            SOUND.play("flip")

    def _tick_glow(self):
        self._glow_phase = (self._glow_phase + 0.08) % (2 * math.pi)
        self.number_widget.set_glow(0.5 + 0.5 * math.sin(self._glow_phase))

    def _finish(self):
        self.glow_timer.stop()
        self.finished_signal.emit()
        self.accept()

    def _fade_in(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade.setDuration(250)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.start()


class NumberRoulette(QWidget):
    """SuspensePopup 안에서 큰 숫자를 그리는 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.number = 0
        self.glow = 0.5
        self.is_final = False
        self.setMinimumHeight(180)

    def set_number(self, n, final=False):
        self.number = n
        self.is_final = final
        self.update()

    def set_glow(self, g):
        self.glow = g
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()

        # 후광 (radial gradient)
        glow_radius = 100 + 30 * self.glow
        glow = QRadialGradient(cx, cy, glow_radius)
        if self.is_final:
            glow.setColorAt(0, QColor(255, 215, 0, 200))
            glow.setColorAt(0.5, QColor(255, 200, 0, 80))
            glow.setColorAt(1, QColor(255, 200, 0, 0))
        else:
            alpha = int(120 + 60 * self.glow)
            glow.setColorAt(0, QColor(255, 215, 0, alpha))
            glow.setColorAt(0.6, QColor(255, 200, 0, 30))
            glow.setColorAt(1, QColor(255, 200, 0, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.NoPen)
        p.drawEllipse(int(cx - glow_radius), int(cy - glow_radius),
                      int(glow_radius * 2), int(glow_radius * 2))

        # 숫자 그림자
        font_size = 110 if self.is_final else 96
        f = QFont("Georgia", font_size, QFont.Black)
        p.setFont(f)
        text = f"{self.number:03d}"

        # 그림자
        p.setPen(QColor(0, 0, 0, 180))
        p.drawText(rect.adjusted(3, 3, 3, 3), Qt.AlignCenter, text)

        # 황금 그라데이션 텍스트
        grad = QLinearGradient(0, cy - 50, 0, cy + 50)
        if self.is_final:
            grad.setColorAt(0, QColor("#FFE48A"))
            grad.setColorAt(0.5, QColor("#FFD700"))
            grad.setColorAt(1, QColor("#B8860B"))
        else:
            grad.setColorAt(0, QColor("#FFE48A"))
            grad.setColorAt(1, QColor("#C9A227"))
        p.setPen(QPen(QBrush(grad), 1))
        p.setBrush(QBrush(grad))

        # 텍스트를 path로 변환해서 그라데이션 채우기
        path = QPainterPath()
        path.addText(0, 0, f, text)
        # 중앙 정렬
        bounds = path.boundingRect()
        path.translate(cx - bounds.center().x(), cy - bounds.center().y())
        p.fillPath(path, QBrush(grad))
        # 외곽선
        p.setPen(QPen(QColor("#5a4510"), 2))
        p.drawPath(path)


# =============================================================================
# 결과 팝업 (당첨 시 화려하게)
# =============================================================================
class ResultPopup(QDialog):
    def __init__(self, card_number, prize_or_none, parent=None):
        super().__init__(parent)
        self.is_winner = prize_or_none is not None
        self.prize = prize_or_none
        self.card_number = card_number
        self.setFixedSize(420, 360)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._build()
        self._fade_in()

    def _build(self):
        # 외곽 컨테이너
        container = QFrame(self)
        container.setGeometry(0, 0, 420, 360)
        if self.is_winner:
            container.setStyleSheet(f"""
                QFrame {{
                    background: {COLOR_BG};
                    border: 3px solid {COLOR_GOLD};
                    border-radius: 14px;
                }}
            """)
        else:
            container.setStyleSheet(f"""
                QFrame {{
                    background: {COLOR_BG};
                    border: 2px solid #555;
                    border-radius: 14px;
                }}
            """)

        v = QVBoxLayout(container)
        v.setContentsMargins(30, 25, 30, 25)
        v.setSpacing(10)

        # 제목
        if self.is_winner:
            title = QLabel("🎊  당  첨  🎊")
            title.setStyleSheet(f"color: {COLOR_GOLD_LIGHT}; font-size: 26px; font-weight: bold; background: transparent; border: none;")
        else:
            title = QLabel("꽝")
            title.setStyleSheet(f"color: #888; font-size: 22px; font-weight: bold; background: transparent; border: none;")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        # 카드 번호
        num = QLabel(f"#{self.card_number:03d}")
        num.setAlignment(Qt.AlignCenter)
        if self.is_winner:
            num.setStyleSheet(f"color: {COLOR_GOLD}; font-size: 56px; font-weight: 900; font-family: Georgia; background: transparent; border: none;")
        else:
            num.setStyleSheet(f"color: #666; font-size: 56px; font-weight: 900; font-family: Georgia; background: transparent; border: none;")
        v.addWidget(num)

        # 결과
        if self.is_winner:
            result = QLabel(self.prize["name"])
            result.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        else:
            result = QLabel("랜덤굿즈")
            result.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 14px; background: transparent; border: none;")
        result.setAlignment(Qt.AlignCenter)
        v.addWidget(result)

        # 이미지 (당첨일 경우)
        if self.is_winner and self.prize.get("image") and os.path.exists(self.prize["image"]):
            img = QLabel()
            pix = QPixmap(self.prize["image"]).scaled(160, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img.setPixmap(pix)
            img.setAlignment(Qt.AlignCenter)
            img.setStyleSheet("background: transparent; border: none;")
            v.addWidget(img)
        else:
            v.addStretch()

        # 확인 버튼
        btn = QPushButton("확인")
        btn.setCursor(Qt.PointingHandCursor)
        if self.is_winner:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_GOLD};
                    color: black;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 10px 30px;
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{ background: {COLOR_GOLD_LIGHT}; }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #444;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 10px 30px;
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{ background: #555; }}
            """)
        btn.clicked.connect(self.accept)
        v.addWidget(btn, alignment=Qt.AlignCenter)

    def _fade_in(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade.setDuration(280)
        self.fade.setStartValue(0.0)
        self.fade.setEndValue(1.0)
        self.fade.setEasingCurve(QEasingCurve.OutCubic)
        self.fade.start()


# =============================================================================
# 메인 윈도우
# =============================================================================
class KujinoMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.cards = []  # ShieldCard 위젯 목록
        self.selected_card = None
        self.is_muted = False
        self.setWindowTitle("KUJINO - 쿠지노")
        self.setMinimumSize(1300, 820)
        self.setStyleSheet(f"QMainWindow {{ background: {COLOR_BG}; }}")
        # 앱 아이콘 설정 (작업 표시줄에 표시됨)
        if os.path.exists(LOGO_PATH):
            self.setWindowIcon(QIcon(LOGO_PATH))
        self._build_ui()
        self._refresh_all()
        # 파티클 오버레이 (모든 위젯 위에 떠있음)
        self.sparkle = SparkleOverlay(self)
        self.sparkle.setGeometry(self.rect())
        self.sparkle.raise_()
        self.sparkle.show()
        # BGM 자동 시작 (파일이 있을 때만)
        QTimer.singleShot(500, SOUND.play_bgm)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 진행률 바 다시 계산
        QTimer.singleShot(0, lambda: self.progress.update_stats(self.dm.stats()))
        # 파티클 오버레이도 윈도우 전체에 맞게
        if hasattr(self, 'sparkle'):
            self.sparkle.setGeometry(self.rect())
            self.sparkle.raise_()

    def _build_ui(self):
        central = QWidget()
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # 좌측 사이드바: 당첨 결과
        h.addWidget(self._build_left_sidebar(), stretch=0)

        # 중앙: 메인 콘텐츠
        h.addWidget(self._build_main_area(), stretch=1)

        # 우측 사이드바: 남은 상품
        h.addWidget(self._build_right_sidebar(), stretch=0)

        self.setCentralWidget(central)

    # -------------------------------------------------------------------------
    # 좌측 사이드바 (파란 박스: 당첨 결과)
    # -------------------------------------------------------------------------
    def _build_left_sidebar(self):
        w = QWidget()
        w.setFixedWidth(240)
        w.setStyleSheet(f"background: {COLOR_PANEL}; border-right: 1px solid {COLOR_BORDER};")

        v = QVBoxLayout(w)
        v.setContentsMargins(12, 70, 12, 12)  # 위쪽 여백은 로고 자리
        v.setSpacing(10)

        # 당첨 결과 헤더
        header = QFrame()
        header.setStyleSheet(f"QFrame {{ background: transparent; border: none; }}")
        hh = QHBoxLayout(header)
        hh.setContentsMargins(0, 0, 0, 0)

        trophy = QLabel("🏆")
        trophy.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        hh.addWidget(trophy)
        title = QLabel("당첨 결과")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 15px; font-weight: bold; background: transparent; border: none;")
        hh.addWidget(title)
        hh.addStretch()
        self.winner_count = QLabel("0건")
        self.winner_count.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px; background: transparent; border: none;")
        hh.addWidget(self.winner_count)
        v.addWidget(header)

        # 당첨 리스트
        self.winner_list = QListWidget()
        self.winner_list.setStyleSheet(f"""
            QListWidget {{
                background: #15110a;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #2a1f10;
                background: #1a1308;
                margin: 2px 0;
                border-radius: 4px;
            }}
        """)
        v.addWidget(self.winner_list, stretch=1)

        return w

    # -------------------------------------------------------------------------
    # 메인 영역
    # -------------------------------------------------------------------------
    def _build_main_area(self):
        w = QWidget()
        w.setStyleSheet(f"background: {COLOR_BG};")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 상단 바 (로고 + 정보 박스)
        top_bar = QFrame()
        top_bar.setFixedHeight(80)
        top_bar.setStyleSheet(f"QFrame {{ background: #0a0805; border-bottom: 1px solid {COLOR_BORDER}; }}")
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(15, 8, 15, 8)
        tb.setSpacing(15)

        # 로고
        self.logo = KujinoLogo()
        tb.addWidget(self.logo)

        tb.addStretch()

        # 정보 박스 (가격/계좌)
        self.info_boxes = InfoBoxes()
        self.info_boxes.edit_requested.connect(self.open_repair)
        tb.addWidget(self.info_boxes)

        v.addWidget(top_bar)

        # 콘텐츠 영역
        content = QWidget()
        cv = QVBoxLayout(content)
        cv.setContentsMargins(20, 15, 20, 15)
        cv.setSpacing(12)

        # 쿠지 제목 + 진행률
        title_row = QHBoxLayout()
        title_row.setSpacing(15)

        self.title_label = QPushButton("")
        self.title_label.setCursor(Qt.PointingHandCursor)
        self.title_label.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_GOLD};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Malgun Gothic', sans-serif;
                background: transparent;
                border: none;
                text-align: left;
                padding: 4px 8px;
            }}
            QPushButton:hover {{ color: {COLOR_GOLD_LIGHT}; }}
        """)
        self.title_label.clicked.connect(self.open_repair)
        title_row.addWidget(self.title_label)
        title_row.addStretch()
        cv.addLayout(title_row)

        # 진행률 바
        self.progress = ProgressPanel()
        cv.addWidget(self.progress)

        # 컨트롤 바 (선택해제 / 섞기 / 오픈 / 번호 입력)
        ctrl_bar = self._build_control_bar()
        cv.addWidget(ctrl_bar)

        # 카드 그리드 (스크롤)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: #0f0a05;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QScrollBar:vertical {{ background: #1a1308; width: 10px; }}
            QScrollBar::handle:vertical {{
                background: {COLOR_GOLD_DARK}; border-radius: 5px; min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        grid_w = QWidget()
        grid_w.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(grid_w)
        self.grid.setSpacing(6)
        self.grid.setContentsMargins(15, 15, 15, 15)

        # 카드 위젯들 생성 (현재 카드 수 기준)
        self._rebuild_card_grid()

        scroll.setWidget(grid_w)
        cv.addWidget(scroll, stretch=1)

        v.addWidget(content, stretch=1)
        return w

    def _rebuild_card_grid(self):
        """카드 그리드 재생성 (카드 수가 바뀌면 호출)"""
        # 기존 카드 위젯 제거
        for card in self.cards:
            card.setParent(None)
            card.deleteLater()
        self.cards.clear()
        self.selected_card = None

        # 새 카드 생성
        total = self.dm.total_cards()
        # 카드 수에 따라 컬럼 수 조정 (작을수록 컬럼 줄임)
        if total <= 20:
            cols = 5
        elif total <= 49:
            cols = 7
        elif total <= 81:
            cols = 9
        else:
            cols = 9
        for i in range(total):
            number = i + 1
            card = ShieldCard(number)
            card.clicked.connect(lambda _, c=card: self.on_card_clicked(c))
            self.cards.append(card)
            self.grid.addWidget(card, i // cols, i % cols)

    def _build_control_bar(self):
        bar = QFrame()
        bar.setStyleSheet(f"QFrame {{ background: transparent; border: none; }}")
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        # ========== 1행: 핵심 뽑기 컨트롤 ==========
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        # 선택해제
        self.deselect_btn = self._mk_btn("✕ 선택해제", "#888")
        self.deselect_btn.clicked.connect(self.deselect)
        row1.addWidget(self.deselect_btn)

        # 섞기
        self.shuffle_btn = self._mk_btn("🔀 섞기", COLOR_PURPLE)
        self.shuffle_btn.clicked.connect(self.shuffle)
        row1.addWidget(self.shuffle_btn)

        # 오픈 (메인 액션 - 크게)
        self.open_btn = self._mk_btn("▶  오픈 (0)", COLOR_GOLD, dark_text=True)
        self.open_btn.setMinimumWidth(120)
        self.open_btn.clicked.connect(self.open_selected)
        row1.addWidget(self.open_btn)

        # 번호 입력
        row1.addSpacing(10)
        num_lbl = QLabel("번호:")
        num_lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 13px;")
        row1.addWidget(num_lbl)

        self.num_input = QLineEdit()
        self.num_input.setPlaceholderText("1~100")
        self.num_input.setFixedWidth(75)
        self.num_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
            }}
        """)
        self.num_input.returnPressed.connect(self.select_by_number)
        row1.addWidget(self.num_input)

        select_btn = self._mk_btn("🔍 선택", "#4CAF50")
        select_btn.clicked.connect(self.select_by_number)
        row1.addWidget(select_btn)

        row1.addStretch()

        # 사운드 토글 (1행 끝)
        self.mute_btn = self._mk_btn("🔊", "#444")
        self.mute_btn.setFixedWidth(45)
        self.mute_btn.setToolTip("음소거 토글")
        self.mute_btn.clicked.connect(self.toggle_mute)
        row1.addWidget(self.mute_btn)

        # BGM 토글
        self.bgm_btn = self._mk_btn("🎵", "#444")
        self.bgm_btn.setFixedWidth(45)
        self.bgm_btn.setToolTip("배경 음악 ON/OFF")
        self.bgm_btn.clicked.connect(self.toggle_bgm)
        row1.addWidget(self.bgm_btn)

        outer.addLayout(row1)

        # ========== 2행: 세션 / 데이터 관리 ==========
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        # 세션 저장
        self.save_btn = self._mk_btn("💾 세션 저장", COLOR_GREEN)
        self.save_btn.setToolTip("현재 진행 상태를 이름 붙여 저장")
        self.save_btn.clicked.connect(self.save_session)
        row2.addWidget(self.save_btn)

        # 세션 불러오기
        self.load_btn = self._mk_btn("📂 불러오기", COLOR_BLUE)
        self.load_btn.setToolTip("저장된 세션 목록")
        self.load_btn.clicked.connect(self.load_session)
        row2.addWidget(self.load_btn)

        # 결과 내보내기 (텍스트)
        self.export_btn = self._mk_btn("📋 결과 내보내기", "#666")
        self.export_btn.setToolTip("뽑기 결과를 텍스트 파일로 저장")
        self.export_btn.clicked.connect(self.export_results)
        row2.addWidget(self.export_btn)

        row2.addStretch()

        # 새 게임
        self.new_btn = self._mk_btn("↻ 새 게임", "#555")
        self.new_btn.setToolTip("모든 카드를 처음부터 다시 시작")
        self.new_btn.clicked.connect(self.new_game)
        row2.addWidget(self.new_btn)

        outer.addLayout(row2)

        return bar

    def _mk_btn(self, text, color, dark_text=False):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(36)
        text_color = "#000" if dark_text else "#fff"
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: {text_color};
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{ background: {color}; opacity: 0.85; }}
            QPushButton:pressed {{ padding-top: 8px; }}
        """)
        return btn

    # -------------------------------------------------------------------------
    # 우측 사이드바 (남은 상품)
    # -------------------------------------------------------------------------
    def _build_right_sidebar(self):
        w = QWidget()
        w.setFixedWidth(280)
        w.setStyleSheet(f"background: {COLOR_PANEL}; border-left: 1px solid {COLOR_BORDER};")

        v = QVBoxLayout(w)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(10)

        # 헤더
        header = QHBoxLayout()
        icon = QLabel("📦")
        icon.setStyleSheet("font-size: 16px;")
        header.addWidget(icon)
        title = QLabel("남은 상품")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 15px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        v.addLayout(header)

        # 상품 카드 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: #15110a; width: 8px; }}
            QScrollBar::handle:vertical {{ background: {COLOR_GOLD_DARK}; border-radius: 4px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self.prize_container = QWidget()
        self.prize_container.setStyleSheet("background: transparent;")
        self.prize_layout = QVBoxLayout(self.prize_container)
        self.prize_layout.setContentsMargins(0, 0, 0, 0)
        self.prize_layout.setSpacing(8)
        self.prize_layout.addStretch()
        scroll.setWidget(self.prize_container)
        v.addWidget(scroll, stretch=1)

        # 쿠지판 수리하기 버튼
        repair_btn = QPushButton("🔧  쿠지판 수리하기")
        repair_btn.setCursor(Qt.PointingHandCursor)
        repair_btn.setMinimumHeight(40)
        repair_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_GOLD};
                color: black;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: {COLOR_GOLD_LIGHT}; }}
        """)
        repair_btn.clicked.connect(self.open_repair)
        v.addWidget(repair_btn)

        return w

    # -------------------------------------------------------------------------
    # 동작 / 이벤트
    # -------------------------------------------------------------------------
    def on_card_clicked(self, card):
        if card.is_opened:
            QMessageBox.information(self, "안내", f"#{card.number:03d} 카드는 이미 열렸습니다.")
            return
        # 이전 선택 해제
        if self.selected_card and self.selected_card is not card:
            self.selected_card.set_selected(False)
        # 토글
        if self.selected_card is card:
            card.set_selected(False)
            self.selected_card = None
        else:
            card.set_selected(True)
            self.selected_card = card
            SOUND.play("click")
        self._update_open_button()

    def deselect(self):
        if self.selected_card:
            self.selected_card.set_selected(False)
            self.selected_card = None
        self._update_open_button()

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        SOUND.set_muted(self.is_muted)
        self.mute_btn.setText("🔇" if self.is_muted else "🔊")

    def toggle_bgm(self):
        playing = SOUND.toggle_bgm()
        # 아이콘만 바꿔서 표시
        self.bgm_btn.setText("🎶" if playing else "🎵")

    def save_session(self):
        """현재 진행 상태를 이름 붙여 저장"""
        dlg = SessionManagerDialog(self.dm, SessionManagerDialog.SAVE_MODE, self)
        dlg.exec_()

    def load_session(self):
        """저장된 세션 목록에서 선택하여 불러오기"""
        dlg = SessionManagerDialog(self.dm, SessionManagerDialog.LOAD_MODE, self)
        if dlg.exec_() == QDialog.Accepted and dlg.action_taken in ("load", "import"):
            # 카드 수가 변했을 가능성 → 그리드 재생성
            self._rebuild_card_grid()
            self._refresh_all()
            QMessageBox.information(self, "완료", "불러오기 성공!")

    def select_by_number(self):
        text = self.num_input.text().strip()
        total = self.dm.total_cards()
        if not text.isdigit():
            QMessageBox.warning(self, "안내", f"숫자를 입력하세요 (1~{total}).")
            return
        n = int(text)
        if not (1 <= n <= total):
            QMessageBox.warning(self, "안내", f"1~{total} 사이의 번호를 입력하세요.")
            return
        card = self.cards[n - 1]
        if card.is_opened:
            QMessageBox.information(self, "안내", f"#{n:03d} 카드는 이미 열렸습니다.")
            return
        if self.selected_card and self.selected_card is not card:
            self.selected_card.set_selected(False)
        card.set_selected(True)
        self.selected_card = card
        self.num_input.clear()
        self._update_open_button()

    def open_selected(self):
        if not self.selected_card:
            QMessageBox.information(self, "안내", "먼저 카드를 선택하세요.\n(카드를 클릭하거나 번호를 입력)")
            return
        card = self.selected_card
        card_data = self.dm.data["cards"][card.number - 1]
        prize_number = card_data["prize_number"]
        prize = self.dm.find_prize(prize_number)

        # 데이터 갱신
        card_data["opened"] = True
        self.dm.save()
        self.selected_card = None
        self._update_open_button()

        # === 1. 긴장감 팝업 (룰렛 효과) ===
        suspense = SuspensePopup(card.number, self.dm.total_cards(), self)
        suspense.finished_signal.connect(
            lambda: self._reveal_card(card, prize)
        )
        suspense.exec_()

    def _reveal_card(self, card, prize):
        """긴장감 팝업이 끝난 후: 카드 뒤집기 + 파티클 + 결과 팝업"""
        # === 2. 카드 뒤집기 애니메이션 ===
        card.open_card(is_winner=(prize is not None))
        SOUND.play("flip")

        # === 3. 파티클 효과 ===
        # 카드 위치 (오버레이 좌표계로 변환)
        card_global = card.mapTo(self, card.rect().center())
        if prize is not None:
            # 당첨: 화려한 황금 폭발 + 콘페티 비
            self.sparkle.burst(
                card_global.x(), card_global.y(),
                count=60, palette="gold", strength=14, shape="star"
            )
            QTimer.singleShot(200, lambda: self.sparkle.confetti_rain(count=80))
            QTimer.singleShot(400, lambda: self.sparkle.burst(
                card_global.x(), card_global.y(),
                count=30, palette="colorful", strength=10, shape="confetti"
            ))
        else:
            # 꽝: 소박한 작은 효과
            self.sparkle.burst(
                card_global.x(), card_global.y(),
                count=15, palette="gold", strength=6, shape="sparkle"
            )

        # === 4. 결과 팝업 ===
        QTimer.singleShot(700, lambda: self._show_result(card.number, prize))

    def _show_result(self, card_number, prize):
        # 당첨 시 추가 사운드 + 결과 팝업 옆에서 콘페티 한 번 더
        if prize is not None:
            SOUND.play("win")
            QTimer.singleShot(100, lambda: self.sparkle.confetti_rain(count=60))
        else:
            SOUND.play("lose")

        dlg = ResultPopup(card_number, prize, self)
        dlg.exec_()
        self._refresh_all()

    def _update_open_button(self):
        n = 1 if self.selected_card else 0
        self.open_btn.setText(f"▶  오픈 ({n})")

    def shuffle(self):
        reply = QMessageBox.question(
            self, "섞기",
            "아직 열리지 않은 카드들의 상품 위치를 섞습니다. 진행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        SOUND.play("shuffle")
        self.dm.shuffle_unopened()
        self.dm.save()
        # 섞기 효과: 미니 파티클
        if hasattr(self, 'sparkle'):
            cx = self.width() // 2
            cy = self.height() // 2
            self.sparkle.burst(cx, cy, count=25, palette="gold",
                              strength=8, shape="sparkle")
        QMessageBox.information(self, "완료", "남은 카드들을 섞었습니다.")

    def new_game(self):
        reply = QMessageBox.question(
            self, "새 게임",
            "모든 카드를 처음부터 다시 시작합니다.\n뽑기 기록이 모두 사라집니다. 진행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.dm.reset_all()
        self.dm.save()
        for card in self.cards:
            card.reset()
        self.selected_card = None
        self._refresh_all()

    def open_repair(self):
        old_total = self.dm.total_cards()
        dlg = RepairDialog(self.dm, self)
        if dlg.exec_() == QDialog.Accepted:
            # 카드 수가 변경되면 그리드 재생성
            if self.dm.total_cards() != old_total:
                self._rebuild_card_grid()
            self._refresh_all()

    def export_results(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "결과 저장", "kujino_results.txt", "Text Files (*.txt)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("=" * 50 + "\n")
                f.write(f"  {self.dm.data['title']}\n")
                f.write("=" * 50 + "\n\n")
                stats = self.dm.stats()
                f.write(f"전체 {stats['total']}장 / 오픈 {stats['opened']}장 / 남은 {stats['remaining']}장 ({stats['percent']}%)\n\n")
                f.write("당첨 결과:\n")
                for w in self.dm.winners():
                    f.write(f"  #{w['number']:03d}  →  {w['prize']['name']}\n")
                f.write("\n전체 뽑기 기록:\n")
                for d in self.dm.all_drawn():
                    f.write(f"  #{d['number']:03d}  →  {d['prize_name']}\n")
            QMessageBox.information(self, "완료", f"저장되었습니다:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    # -------------------------------------------------------------------------
    # 화면 갱신
    # -------------------------------------------------------------------------
    def _refresh_all(self):
        # 제목
        self.title_label.setText(f"  {self.dm.data['title']}  ✎")

        # 정보 박스
        self.info_boxes.update_values(
            self.dm.data["price_account"],
            self.dm.data["price_store"],
            self.dm.data["bank"]
        )

        # 번호 입력 placeholder 갱신
        if hasattr(self, 'num_input'):
            self.num_input.setPlaceholderText(f"1~{self.dm.total_cards()}")

        # 진행률
        stats = self.dm.stats()
        self.progress.update_stats(stats)

        # 카드 상태 동기화
        for i, card in enumerate(self.cards):
            data = self.dm.data["cards"][i]
            if data["opened"] and not card.is_opened:
                card.is_opened = True
                card.is_winner = data["prize_number"] > 0
                card._flip = 1.0
                card.update()
            elif not data["opened"] and card.is_opened:
                card.reset()

        # 당첨 결과 리스트
        self.winner_list.clear()
        winners = self.dm.winners()
        self.winner_count.setText(f"{len(winners)}건")
        for w in winners:
            item = QListWidgetItem(f"  {w['number']:>3}    {w['prize']['name']}")
            item.setForeground(QColor(COLOR_GOLD_LIGHT))
            self.winner_list.addItem(item)

        # 남은 상품 패널
        # 기존 위젯 제거
        while self.prize_layout.count() > 1:
            item = self.prize_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for prize in self.dm.data["prizes"]:
            remaining = self.dm.prize_remaining(prize["number"])
            card = PrizeCard(prize, remaining)
            self.prize_layout.insertWidget(self.prize_layout.count() - 1, card)


# =============================================================================
# 진입점
# =============================================================================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = KujinoMainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
