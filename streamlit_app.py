import random
import time
import math
import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Classic Sudoku",
    page_icon="🔢",
    layout="wide"
)

SYMBOLS = "123456789ABCDEFG"
DIFFICULTIES = ["하", "중", "상", "최상"]
CLUES = {"하": 26, "중": 23, "상": 20, "최상": 17}
MIN_CLUES = {9: 17, 16: 40}
TURN_SECONDS = 20

SEED = [
    [int(x) for x in row]
    for row in [
        "000000010", "400000000", "020000000",
        "000050407", "008000300", "001090000",
        "300400200", "050100000", "000806000"
    ]
]

# =========================================================
# CSS - 이미지(Classic Sudoku) 형식: 흰 칸 + 얇은 회색선 + 굵은 검은 구역선
# =========================================================

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding: 1rem 0.6rem;
}

div.stButton > button {
    width: 100%;
    min-height: 42px;
    font-size: 16px;
}

/* 타이머 */
.timer-outer {
    width: 100%;
    height: 18px;
    background: #dedede;
    border-radius: 10px;
    overflow: hidden;
    margin: 8px 0 12px 0;
}

.timer-inner {
    height: 100%;
    border-radius: 10px;
}

.player-label {
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    margin: 8px 0;
}

.rule-card {
    padding: 16px;
    border: 1px solid #b8c8dc;
    border-radius: 10px;
    background: #f0f6ff;
    color: #24364c;
    line-height: 1.9;
}

/* 남은 숫자 */
.remaining-number {
    border: 1px solid #b5c7df;
    border-radius: 5px;
    text-align: center;
    padding: 5px 1px;
    background: #edf5ff;
    color: #28548e;
    line-height: 1.2;
}

.remaining-number .digit {
    font-size: 22px;
    font-weight: 700;
}

.remaining-number .count {
    font-size: 12px;
    margin-top: 4px;
    color: #52657d;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# 스도쿠 풀이 엔진
# =========================================================

def candidates(board, r, c, n, box):
    used = set(board[r])
    used.update(board[i][c] for i in range(n))

    br = (r // box) * box
    bc = (c // box) * box

    for i in range(br, br + box):
        for j in range(bc, bc + box):
            used.add(board[i][j])

    return set(range(1, n + 1)) - used


def find_empty(board, n, box):
    best = None
    best_options = None

    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                continue

            options = candidates(board, r, c, n, box)

            if not options:
                return r, c, set()

            if best is None or len(options) < len(best_options):
                best = (r, c)
                best_options = options

                if len(options) == 1:
                    return r, c, options

    if best is None:
        return None, None, None

    return best[0], best[1], best_options


def solve_count(
    board, n, box, limit=2,
    max_nodes=300000, max_seconds=6.0
):
    count = 0
    first_solution = None
    nodes = 0
    start = time.monotonic()
    exhausted = True

    def backtrack():
        nonlocal count, first_solution, nodes, exhausted

        if count >= limit or not exhausted:
            return

        nodes += 1

        if (
            nodes > max_nodes
            or time.monotonic() - start > max_seconds
        ):
            exhausted = False
            return

        r, c, options = find_empty(board, n, box)

        if r is None:
            count += 1
            if first_solution is None:
                first_solution = [row[:] for row in board]
            return

        if not options:
            return

        for value in options:
            board[r][c] = value
            backtrack()
            board[r][c] = 0

            if count >= limit or not exhausted:
                return

    backtrack()
    return count, first_solution, exhausted


def validate(board, n, box):
    for r in range(n):
        values = [v for v in board[r] if v != 0]
        if len(values) != len(set(values)):
            return False, f"{r+1}행에 중복 숫자가 있습니다."

    for c in range(n):
        values = [
            board[r][c] for r in range(n)
            if board[r][c] != 0
        ]
        if len(values) != len(set(values)):
            return False, f"{c+1}열에 중복 숫자가 있습니다."

    for br in range(0, n, box):
        for bc in range(0, n, box):
            values = [
                board[r][c]
                for r in range(br, br + box)
                for c in range(bc, bc + box)
                if board[r][c] != 0
            ]
            if len(values) != len(set(values)):
                return False, "같은 구역에 중복 숫자가 있습니다."

    return True, ""


# =========================================================
# 문제 생성
# =========================================================

@st.cache_resource
def get_seed_solution():
    """기본 퍼즐의 유일해 검증은 앱 실행 후 딱 한 번만 수행한다."""
    count, solution, complete = solve_count(
        [row[:] for row in SEED], 9, 3, limit=2, max_seconds=30.0
    )

    if count != 1 or not complete:
        raise RuntimeError("기본 퍼즐의 유일해 검증에 실패했습니다.")

    return solution


def generate_puzzle(target_clues):
    seed_solution = get_seed_solution()

    def shuffled_groups():
        groups = [
            list(range(3 * i, 3 * i + 3))
            for i in range(3)
        ]
        random.shuffle(groups)
        return [
            v for group in groups
            for v in random.sample(group, 3)
        ]

    rows = shuffled_groups()
    cols = shuffled_groups()

    digits = list(range(1, 10))
    random.shuffle(digits)
    mapping = {i + 1: digits[i] for i in range(9)}

    transpose = random.choice([True, False])

    def transform(board):
        result = [[board[r][c] for c in cols] for r in rows]

        if transpose:
            result = [list(row) for row in zip(*result)]

        return [
            [mapping[v] if v else 0 for v in row]
            for row in result
        ]

    puzzle = transform(SEED)
    solution = transform(seed_solution)

    empty = [
        (r, c)
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] == 0
    ]
    random.shuffle(empty)

    for r, c in empty[:target_clues - 17]:
        puzzle[r][c] = solution[r][c]

    assert sum(v != 0 for row in puzzle for v in row) == target_clues

    return puzzle, solution


# =========================================================
# 입력 상태 초기화
# =========================================================

def prepare_board(board, mode):
    st.session_state.board = [row[:] for row in board]
    st.session_state.selected = None
    st.session_state.board_mode = mode


# =========================================================
# 1vs1 퍼즐 생성
# =========================================================

def make_versus_level():
    difficulty = DIFFICULTIES[st.session_state.level_index]
    puzzle, solution = generate_puzzle(CLUES[difficulty])

    prepare_board(puzzle, "versus")
    st.session_state.solution = solution

    st.session_state.locked = {
        (r, c)
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] != 0
    }

    st.session_state.locked_values = {
        (r, c): puzzle[r][c]
        for r in range(9)
        for c in range(9)
        if puzzle[r][c] != 0
    }

    now = time.time()
    st.session_state.turn_start = now
    st.session_state.deadline = now + TURN_SECONDS
    st.session_state.phase = "active"


def finish_versus(loser, reason):
    st.session_state.winner = 3 - loser
    st.session_state.phase = "finished"
    st.session_state.finish_reason = reason


# =========================================================
# 입력 콜백
# =========================================================

def handle_cell_input(r, c, value, mode):
    """판(컴포넌트)에서 들어온 입력 처리. value 0 은 지우기."""
    # 처음 주어진 단서는 선택만 가능하고 수정은 불가능
    if (r, c) in st.session_state.get("locked", set()):
        return

    if mode == "solve":
        st.session_state.board[r][c] = value
        st.session_state.solve_result = None
        return

    if value == 0:
        return

    if mode == "puzzle":
        if st.session_state.game_over:
            return

        if st.session_state.board[r][c] != 0:
            return

        if value == st.session_state.solution[r][c]:
            st.session_state.board[r][c] = value
        else:
            st.session_state.lives -= 1

            if st.session_state.lives <= 0:
                st.session_state.lives = 0
                st.session_state.game_over = True
        return

    if mode == "versus":
        if st.session_state.phase != "active":
            return

        # 20초를 넘겨서 입력하면 시간 초과 패배
        if time.time() >= st.session_state.deadline:
            finish_versus(st.session_state.player, "시간 초과")
            return

        if st.session_state.board[r][c] != 0:
            return

        # 오답이면 즉시 패배
        if value != st.session_state.solution[r][c]:
            finish_versus(st.session_state.player, "오답")
            return

        st.session_state.board[r][c] = value

        # 판 완성 -> 다음 난이도 (마지막으로 맞힌 플레이어가 그대로 먼저 시작)
        if all(v != 0 for row in st.session_state.board for v in row):
            next_level = st.session_state.level_index + 1

            if next_level >= len(DIFFICULTIES):
                st.session_state.phase = "champion"
                st.session_state.winner = st.session_state.player
                return

            st.session_state.level_index = next_level
            make_versus_level()
            return

        # 정답 -> 상대 턴, 20초 다시 시작
        st.session_state.player = 3 - st.session_state.player
        now = time.time()
        st.session_state.turn_start = now
        st.session_state.deadline = now + TURN_SECONDS


# =========================================================
# 스도쿠 판 출력 (이미지 형식)
#  - 칸은 모두 흰색, 얇은 회색선
#  - 구역(9x9 는 3칸, 16x16 은 4칸)마다 굵은 검은 실선
#  - 칸마다 왼쪽/위쪽 선만 그려서 선이 겹쳐 두꺼워지지 않게 함
# =========================================================

BOARD_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body {
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: "Segoe UI", "Noto Sans KR", "Malgun Gothic", Arial, sans-serif;
  }
  #wrap {
    width: 100%;
    box-sizing: border-box;
    padding: 4px 0 6px 0;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  /* 판: 흰 칸 + 얇은 회색선 + 굵은 검은 구역선 (Classic Sudoku 양식) */
  #grid {
    display: grid;
    background: #ffffff;
    outline: none;
    user-select: none;
    -webkit-user-select: none;
    touch-action: manipulation;
  }
  .cell {
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #ffffff;
    color: #111111;
    cursor: pointer;
    line-height: 1;
    overflow: hidden;
  }
  .cell.given { font-weight: 800; color: #111111; }
  .cell.user  { font-weight: 600; color: #1a56c4; }
  .cell.sel   { background: #ffe98a; }

  #pad {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px;
    margin-top: 12px;
    max-width: 680px;
  }
  #pad button {
    min-width: 36px;
    height: 40px;
    padding: 0 8px;
    font-size: 17px;
    font-weight: 700;
    color: #111111;
    background: #ffffff;
    border: 1px solid #8c8c8c;
    border-radius: 6px;
    cursor: pointer;
  }
  #pad button:active { background: #ffe98a; }
  #pad.off button { opacity: 0.45; cursor: default; }
</style>
</head>
<body>
<div id="wrap">
  <div id="grid" tabindex="0"></div>
  <div id="pad"></div>
</div>

<script>
(function () {
  var SYMBOLS = "123456789ABCDEFG";
  var args = null;
  var selected = null;
  var counter = 0;
  var lastHeight = 0;
  var padKey = "";

  var wrap = document.getElementById("wrap");
  var grid = document.getElementById("grid");
  var pad = document.getElementById("pad");

  function send(type, data) {
    var msg = { isStreamlitMessage: true, type: type };
    for (var k in data) { msg[k] = data[k]; }
    window.parent.postMessage(msg, "*");
  }

  function setHeight() {
    var h = wrap.offsetHeight + 8;
    if (h !== lastHeight) {
      lastHeight = h;
      send("streamlit:setFrameHeight", { height: h });
    }
  }

  function sendInput(v) {
    if (!args || !selected || !args.enabled) return;
    if (v === 0 && !args.allow_erase) return;

    var r = selected[0], c = selected[1];
    if (args.given[r][c]) return;              // 처음 단서는 선택만 가능, 수정 불가
    if (args.board[r][c] === v) return;

    counter += 1;
    send("streamlit:setComponentValue", {
      value: { id: Date.now() + "-" + counter, r: r, c: c, v: v },
      dataType: "json"
    });
  }

  function renderGrid() {
    var n = args.n;
    var box = (n === 9) ? 3 : 4;
    var maxW = (n === 9) ? 540 : 680;
    var avail = wrap.clientWidth - 8;
    var size = Math.max(180, Math.min(avail, maxW));
    var cellSize = size / n;

    if (selected && (selected[0] >= n || selected[1] >= n)) selected = null;

    grid.style.width = size + "px";
    grid.style.height = size + "px";
    grid.style.gridTemplateColumns = "repeat(" + n + ", 1fr)";
    grid.style.gridTemplateRows = "repeat(" + n + ", 1fr)";
    grid.style.fontSize = Math.round(cellSize * 0.58) + "px";

    var THIN = "1px solid #9a9a9a";
    var THICK = "3px solid #111111";

    var html = [];
    for (var r = 0; r < n; r++) {
      for (var c = 0; c < n; c++) {
        var v = args.board[r][c];
        var cls = "cell";
        if (args.given[r][c]) cls += " given";
        else if (v) cls += " user";
        if (selected && selected[0] === r && selected[1] === c) cls += " sel";

        var left = (c % box === 0) ? THICK : THIN;
        var top = (r % box === 0) ? THICK : THIN;
        var right = (c === n - 1) ? THICK : "none";
        var bottom = (r === n - 1) ? THICK : "none";

        html.push(
          '<div class="' + cls + '" data-r="' + r + '" data-c="' + c + '" ' +
          'style="border-left:' + left + ";border-top:" + top +
          ";border-right:" + right + ";border-bottom:" + bottom + '">' +
          (v ? SYMBOLS.charAt(v - 1) : "") + "</div>"
        );
      }
    }
    grid.innerHTML = html.join("");
  }

  function buildPad() {
    var key = args.n + ":" + (args.allow_erase ? "e" : "-");
    if (key !== padKey) {
      padKey = key;
      var html = [];
      for (var v = 1; v <= args.n; v++) {
        html.push('<button type="button" data-v="' + v + '">' + SYMBOLS.charAt(v - 1) + "</button>");
      }
      if (args.allow_erase) {
        html.push('<button type="button" data-v="0">⌫</button>');
      }
      pad.innerHTML = html.join("");
    }
    pad.className = args.enabled ? "" : "off";
  }

  function fullRender() {
    renderGrid();
    buildPad();
    window.requestAnimationFrame(setHeight);
  }

  // 셀 선택 (단서 칸도 선택 가능)
  grid.addEventListener("click", function (e) {
    var t = e.target;
    while (t && t !== grid && !(t.classList && t.classList.contains("cell"))) t = t.parentNode;
    if (!t || t === grid) return;
    selected = [parseInt(t.getAttribute("data-r"), 10), parseInt(t.getAttribute("data-c"), 10)];
    renderGrid();
    grid.focus();
  });

  // 숫자 패드 (모바일용)
  pad.addEventListener("mousedown", function (e) { e.preventDefault(); });
  pad.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || t.tagName !== "BUTTON") return;
    sendInput(parseInt(t.getAttribute("data-v"), 10));
  });

  // 키보드
  document.addEventListener("keydown", function (e) {
    if (!args) return;
    var n = args.n;
    var k = e.key;

    var dr = 0, dc = 0, isArrow = true;
    if (k === "ArrowUp") dr = -1;
    else if (k === "ArrowDown") dr = 1;
    else if (k === "ArrowLeft") dc = -1;
    else if (k === "ArrowRight") dc = 1;
    else isArrow = false;

    if (isArrow) {
      e.preventDefault();
      if (!selected) selected = [0, 0];
      else selected = [
        Math.min(n - 1, Math.max(0, selected[0] + dr)),
        Math.min(n - 1, Math.max(0, selected[1] + dc))
      ];
      renderGrid();
      return;
    }

    if (k === "Backspace" || k === "Delete" || k === "0") {
      e.preventDefault();
      sendInput(0);
      return;
    }

    if (k && k.length === 1) {
      var idx = SYMBOLS.indexOf(k.toUpperCase());
      if (idx >= 0 && idx < n) {
        e.preventDefault();
        sendInput(idx + 1);
      }
    }
  });

  window.addEventListener("message", function (e) {
    if (!e.data || e.data.type !== "streamlit:render") return;
    args = e.data.args;
    fullRender();
  });

  window.addEventListener("resize", function () {
    if (args) fullRender();
  });

  send("streamlit:componentReady", { apiVersion: 1 });
})();
</script>
</body>
</html>
"""


def _prepare_component_dir():
    """판 화면(HTML)을 app.py 안에 내장하고, 실행 시 임시 폴더에 파일로 만든다."""
    folder = os.path.join(tempfile.gettempdir(), "classic_sudoku_board")
    os.makedirs(folder, exist_ok=True)

    path = os.path.join(folder, "index.html")
    try:
        with open(path, encoding="utf-8") as f:
            same = f.read() == BOARD_HTML
    except OSError:
        same = False

    if not same:
        with open(path, "w", encoding="utf-8") as f:
            f.write(BOARD_HTML)

    return folder


_sudoku_component = components.declare_component(
    "sudoku_board", path=_prepare_component_dir()
)


def draw_board(n, mode):
    board = st.session_state.board
    locked = st.session_state.get("locked", set())

    given = [
        [1 if (r, c) in locked else 0 for c in range(n)]
        for r in range(n)
    ]

    if mode == "puzzle":
        enabled = not st.session_state.game_over
    elif mode == "versus":
        enabled = st.session_state.phase == "active"
    else:
        enabled = True

    event = _sudoku_component(
        n=n,
        board=board,
        given=given,
        enabled=enabled,
        allow_erase=(mode == "solve"),
        key=f"sudoku_{mode}_{n}",
        default=None,
    )

    if isinstance(event, dict) and event.get("id") != st.session_state.get(
        "last_board_event"
    ):
        st.session_state.last_board_event = event.get("id")

        try:
            r = int(event["r"])
            c = int(event["c"])
            v = int(event["v"])
        except (KeyError, TypeError, ValueError):
            return

        if 0 <= r < n and 0 <= c < n and 0 <= v <= n and enabled:
            handle_cell_input(r, c, v, mode)
            st.rerun()


# =========================================================
# 숫자별 남은 개수
# =========================================================

def show_remaining(n):
    st.markdown("#### 숫자별 남은 개수")

    counts = {
        v: sum(
            cell == v
            for row in st.session_state.board
            for cell in row
        )
        for v in range(1, n + 1)
    }

    cols = st.columns(n, gap="small")

    for i, col in enumerate(cols, start=1):
        remaining = n - counts[i]

        with col:
            st.markdown(
                f"""
                <div class="remaining-number">
                    <div class="digit">{SYMBOLS[i-1]}</div>
                    <div class="count">{remaining}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


# =========================================================
# 20초 타이머 / 카운트다운
#  st_autorefresh 로 페이지 전체를 0.1초마다 다시 그리면
#  판(입력창 81개)이 그려지기도 전에 계속 새로고침되어 판이 안 뜬다.
#  -> 이 부분만 따로 갱신되는 st.fragment 를 사용한다.
# =========================================================

@st.fragment(run_every=0.2)
def timer_fragment():
    if st.session_state.phase != "active":
        return

    remaining = st.session_state.deadline - time.time()

    if remaining <= 0:
        finish_versus(st.session_state.player, "시간 초과")
        st.rerun()  # 앱 전체를 다시 실행해 결과 화면으로 이동
        return

    percent = remaining / TURN_SECONDS * 100
    color = "#e44b4b" if remaining <= 5 else "#4285d4"

    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            font-weight:700;
            margin-bottom:4px;
        ">
            <span>남은 시간</span>
            <span>{remaining:.1f}초</span>
        </div>

        <div class="timer-outer">
            <div class="timer-inner"
                 style="width:{percent}%;background:{color};">
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


@st.fragment(run_every=0.2)
def ready_fragment():
    if st.session_state.phase != "ready":
        return

    remaining = st.session_state.ready_until - time.time()

    if remaining <= 0:
        make_versus_level()
        st.rerun()
        return

    countdown = max(1, math.ceil(remaining))

    st.markdown(
        f"""
        <div style="text-align:center;padding:35px 0;">
            <h2>1 vs 1 스도쿠 대전</h2>
            <div style="font-size:72px;font-weight:800;margin:25px 0;">
                {countdown}
            </div>
            <p style="font-size:18px;">
                잠시 후 Player {st.session_state.player}부터 시작합니다.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# 세션 상태
# =========================================================

defaults = {
    "page": "home",
    "solve_result": None,
    "lives": 3,
    "game_over": False,
    "phase": "rules",
    "level_index": 0,
    "player": 1,
    "winner": None,
    "finish_reason": "",
    "selected": None,
    "locked": set(),
    "locked_values": {},
    "board": [],
    "solution": [],
    "board_mode": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# 홈 화면
# =========================================================

if st.session_state.page == "home":
    st.title("Classic Sudoku")

    a, b = st.columns(2)

    with a:
        if st.button("풀이", type="primary"):
            st.session_state.page = "solve_select"
            st.rerun()

    with b:
        if st.button("문제", type="primary"):
            st.session_state.page = "puzzle_select"
            st.rerun()


# =========================================================
# 풀이 규격 선택
# =========================================================

elif st.session_state.page == "solve_select":
    st.title("스도쿠 풀이")

    n = st.radio(
        "규격 선택",
        [9, 16],
        format_func=lambda x: f"{x} × {x}",
        horizontal=True
    )

    if st.button("빈 판 만들기", type="primary"):
        prepare_board([[0] * n for _ in range(n)], "solve")

        st.session_state.solve_n = n
        st.session_state.solve_result = None
        st.session_state.locked = set()
        st.session_state.locked_values = {}
        st.session_state.page = "solve_board"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 풀이 화면
# =========================================================

elif st.session_state.page == "solve_board":
    n = st.session_state.solve_n

    st.title(f"{n} × {n} 스도쿠")
    st.caption("셀에 숫자를 입력하십시오. 입력한 숫자는 즉시 반영됩니다.")

    draw_board(n, "solve")
    show_remaining(n)

    if st.button("완료", type="primary"):
        board = [row[:] for row in st.session_state.board]
        box = 3 if n == 9 else 4

        clue_count = sum(v != 0 for row in board for v in row)
        valid, reason = validate(board, n, box)

        if not valid:
            st.session_state.solve_result = (
                "불가능", f"규칙 위반: {reason}"
            )

        elif clue_count < MIN_CLUES[n]:
            st.session_state.solve_result = (
                "불가능",
                f"단서 부족: 현재 {clue_count}개입니다. "
                f"최소 {MIN_CLUES[n]}개 이상의 단서가 필요합니다."
            )

        else:
            count, solution, complete = solve_count(
                [row[:] for row in board],
                n, box, limit=2, max_seconds=6.0
            )

            if not complete:
                st.session_state.solve_result = (
                    "불가능",
                    "풀이 검증 시간 초과: 단서를 더 입력한 후 다시 시도해 주십시오."
                )
            elif count == 0:
                st.session_state.solve_result = (
                    "불가능",
                    "규칙 위반: 입력한 단서로는 해답을 만들 수 없습니다."
                )
            elif count >= 2:
                st.session_state.solve_result = (
                    "불가능",
                    "단서 부족: 가능한 해답이 여러 개입니다."
                )
            else:
                st.session_state.solve_result = ("가능", solution)

        st.rerun()

    result = st.session_state.solve_result

    if result:
        if result[0] == "불가능":
            st.error("풀이 불가능")
            st.warning(result[1])
        else:
            st.success("유일한 해답을 찾았습니다.")
            for row in result[1]:
                st.write("　".join(SYMBOLS[v - 1] for v in row))

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 문제 난이도 선택
# =========================================================

elif st.session_state.page == "puzzle_select":
    st.title("스도쿠 문제")

    difficulty = st.radio(
        "난이도 선택",
        DIFFICULTIES,
        horizontal=True
    )

    st.write(f"초기 단서: {CLUES[difficulty]}개")

    if st.button("문제 생성", type="primary"):
        puzzle, solution = generate_puzzle(CLUES[difficulty])

        prepare_board(puzzle, "puzzle")
        st.session_state.solution = solution

        st.session_state.locked = {
            (r, c)
            for r in range(9)
            for c in range(9)
            if puzzle[r][c] != 0
        }

        st.session_state.locked_values = {
            (r, c): puzzle[r][c]
            for r in range(9)
            for c in range(9)
            if puzzle[r][c] != 0
        }

        st.session_state.lives = 3
        st.session_state.game_over = False
        st.session_state.page = "puzzle_play"
        st.rerun()

    st.divider()
    st.markdown("### 1 vs 1 대전")
    st.write(
        f"두 플레이어가 번갈아 한 칸씩 정답을 입력합니다. "
        f"한 턴은 {TURN_SECONDS}초입니다."
    )

    if st.button("1 vs 1 시작", type="primary"):
        st.session_state.level_index = 0
        st.session_state.player = 1
        st.session_state.winner = None
        st.session_state.finish_reason = ""
        st.session_state.phase = "rules"
        st.session_state.page = "versus"
        st.rerun()

    if st.button("처음으로"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# 일반 문제 플레이
# =========================================================

elif st.session_state.page == "puzzle_play":
    st.title("스도쿠 문제")

    st.markdown(
        f"""
        <div style="text-align:center;font-size:30px;margin:10px;">
            {'❤️ ' * st.session_state.lives}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state.game_over:
        st.error("실패했습니다. 목숨을 모두 사용했습니다.")
    else:
        draw_board(9, "puzzle")
        show_remaining(9)

        if all(v != 0 for row in st.session_state.board for v in row):
            if st.session_state.board == st.session_state.solution:
                st.success("정답입니다!")

    a, b = st.columns(2)

    with a:
        if st.button("새 문제"):
            st.session_state.page = "puzzle_select"
            st.rerun()

    with b:
        if st.button("처음으로"):
            st.session_state.page = "home"
            st.rerun()


# =========================================================
# 1vs1 대전
# =========================================================

elif st.session_state.page == "versus":
    st.title("1 vs 1 스도쿠 대전")

    if st.session_state.phase == "rules":
        st.markdown(f"""
        <div class="rule-card">
        <h3>대전 규칙</h3>
        1. Player 1부터 시작합니다.<br>
        2. 각 플레이어에게 한 턴당 {TURN_SECONDS}초가 주어집니다.<br>
        3. 제한 시간 안에 빈칸 한 개를 정확하게 채우면
        상대 플레이어에게 턴이 넘어갑니다.<br>
        4. 틀린 숫자를 입력하거나 {TURN_SECONDS}초 안에 입력하지 못하면
        해당 플레이어가 패배합니다.<br>
        5. 모든 칸을 정확하게 채우면 다음 난이도로 올라갑니다.<br>
        6. 난이도는 하 → 중 → 상 → 최상 순서입니다.<br>
        7. 다음 난이도에서도 마지막으로 성공한 플레이어가
        먼저 시작합니다.
        </div>
        """, unsafe_allow_html=True)

        st.write("첫 번째 판은 하 난이도입니다.")

        if st.button("대전 시작", type="primary"):
            st.session_state.level_index = 0
            st.session_state.player = 1
            st.session_state.phase = "ready"
            st.session_state.ready_until = time.time() + 3
            st.rerun()

    elif st.session_state.phase == "ready":
        ready_fragment()

    elif st.session_state.phase == "active":
        timer_fragment()

        st.markdown(
            f"""
            <div class="player-label">
                Player {st.session_state.player} 차례
            </div>
            """,
            unsafe_allow_html=True
        )

        difficulty = DIFFICULTIES[st.session_state.level_index]

        st.caption(
            f"현재 난이도: {difficulty} "
            f"({st.session_state.level_index + 1}/4)"
        )

        draw_board(9, "versus")
        show_remaining(9)

        st.caption("정답을 입력하면 상대에게 턴이 넘어갑니다.")

    elif st.session_state.phase == "finished":
        st.title("대전 종료")

        winner = st.session_state.winner
        st.error(f"Player {winner} 승리!")

        st.write(
            f"패배 사유: Player {3-winner}의 "
            f"{st.session_state.finish_reason}"
        )

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.session_state.winner = None
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()

    elif st.session_state.phase == "champion":
        st.title("최종 우승")
        st.balloons()

        st.success(
            f"Player {st.session_state.winner} 최종 우승!"
        )

        st.write("하, 중, 상, 최상 모든 난이도를 완료했습니다.")

        if st.button("다시 대전하기", type="primary"):
            st.session_state.phase = "rules"
            st.session_state.page = "versus"
            st.rerun()

        if st.button("메인 화면"):
            st.session_state.page = "home"
            st.rerun()
