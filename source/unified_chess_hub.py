import tkinter as tk
from tkinter import messagebox
import chess
import chess.variant
import random
import math
import time

# ==========================================
# 1. CORE PIECE VALUES & SEARCH CONFIGURATION
# ==========================================

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 325,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

PST = {
    chess.PAWN: [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 15, 25, 35, 35, 25, 10, 10,
         5,  5, 15, 30, 30, 15,  5,  5,
         0,  0, 10, 25, 25, 10,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-25,-25, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    chess.KNIGHT: [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  5, 20, 30, 30, 20,  5,-30,
        -30,  5, 20, 30, 30, 20,  5,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ]
}

THREE_CHECK_PROGRESSION = [0, 150, 600, 150000]

transposition_table = {}
start_time = 0
time_limit = 2.5  
abort_search = False
current_mode = "3check"  
chosen_elo = 2700

# ==========================================
# 2. EVALUATION & SEARCH WORKERS
# ==========================================

def evaluate_board(board) -> int:
    if board.is_game_over():
        outcome = board.outcome()
        if outcome.winner == chess.WHITE: return 150000
        if outcome.winner == chess.BLACK: return -150000
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            val = PIECE_VALUES[piece.piece_type]
            if piece.piece_type in PST:
                idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
                val += PST[piece.piece_type][idx]
            if piece.color == chess.WHITE: score += val
            else: score -= val

    if current_mode == "3check":
        white_checks = 3 - board.remaining_checks[chess.BLACK]
        black_checks = 3 - board.remaining_checks[chess.WHITE]
        score += THREE_CHECK_PROGRESSION[min(white_checks, 3)]
        score -= THREE_CHECK_PROGRESSION[min(black_checks, 3)]
    else:
        current_turn = board.turn
        board.turn = chess.WHITE
        white_mobility = board.legal_moves.count()
        board.turn = chess.BLACK
        black_mobility = board.legal_moves.count()
        board.turn = current_turn
        mobility_weight = 25 if current_mode == "cheetah" else 10
        score += (white_mobility - black_mobility) * mobility_weight

    if board.turn == chess.WHITE and board.is_check(): score -= 80
    if board.turn == chess.BLACK and board.is_check(): score += 80
    return score

def quiescence_search(board, alpha: int, beta: int) -> int:
    global abort_search
    if time.time() - start_time > time_limit:
        abort_search = True
        return alpha if board.turn == chess.WHITE else beta

    stand_pat = evaluate_board(board)
    if board.turn == chess.WHITE:
        if stand_pat >= beta: return beta
        if stand_pat > alpha: alpha = stand_pat
    else:
        if stand_pat <= alpha: return alpha
        if stand_pat < beta: beta = stand_pat

    for move in board.legal_moves:
        if board.is_capture(move) or board.is_check():
            board.push(move)
            score = quiescence_search(board, alpha, beta)
            board.pop()
            if abort_search: return alpha if board.turn == chess.WHITE else beta
            if board.turn == chess.WHITE:
                if score >= beta: return beta
                if score > alpha: alpha = score
            else:
                if score <= alpha: return alpha
                if score < beta: beta = score
    return alpha if board.turn == chess.WHITE else beta

def pvs_search(board, depth: int, alpha: int, beta: int, allow_null=True) -> tuple[int, chess.Move | None]:
    global abort_search
    if depth > 0 and time.time() - start_time > time_limit:
        abort_search = True
        return (alpha if board.turn == chess.WHITE else beta), None

    board_hash = board.zobrist_hash() if hasattr(board, 'zobrist_hash') else hash(board.fen())
    cached_move = None
    
    if board_hash in transposition_table:
        cached_depth, cached_flag, cached_score, cached_move = transposition_table[board_hash]
        if cached_depth >= depth and depth > 0:
            if cached_flag == 0: return cached_score, cached_move
            elif cached_flag == 1 and cached_score <= alpha: return alpha, cached_move
            elif cached_flag == 2 and cached_score >= beta: return beta, cached_move

    if depth == 0 or board.is_game_over():
        return quiescence_search(board, alpha, beta), None

    if allow_null and depth >= 3 and not board.is_check():
        board.push(chess.Move.null())
        null_eval, _ = pvs_search(board, depth - 1 - 2, alpha, beta, allow_null=False)
        board.pop()
        if board.turn == chess.WHITE and null_eval >= beta: return beta, None
        if board.turn == chess.BLACK and null_eval <= alpha: return alpha, None

    best_move = cached_move
    legal_moves = list(board.legal_moves)
    
    def move_priority(m):
        if m == cached_move: return 4
        if board.gives_check(m): return 3
        if board.is_capture(m): return 2
        return 0
    legal_moves.sort(key=move_priority, reverse=True)

    b_search_pv = True

    if board.turn == chess.WHITE:
        max_eval = -math.inf
        for idx, move in enumerate(legal_moves):
            board.push(move)
            if depth >= 3 and idx > 3 and not board.is_capture(move) and not board.is_check():
                reduction = 2 if idx > 8 else 1
                evaluation, _ = pvs_search(board, depth - 1 - reduction, alpha, beta)
            else:
                evaluation = alpha + 1

            if not b_search_pv:
                evaluation, _ = pvs_search(board, depth - 1, alpha, alpha + 1)
                if alpha < evaluation < beta:
                    evaluation, _ = pvs_search(board, depth - 1, alpha, beta)
            else:
                if evaluation == alpha + 1:
                    evaluation, _ = pvs_search(board, depth - 1, alpha, beta)

            board.pop()
            if abort_search: return alpha, best_move
            
            if evaluation > max_eval:
                max_eval = evaluation
                best_move = move
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
            b_search_pv = False
            
        if not abort_search:
            flag = 0 if alpha < max_eval < beta else (1 if max_eval <= alpha else 2)
            transposition_table[board_hash] = (depth, flag, max_eval, best_move)
        return max_eval, best_move
    else:
        min_eval = math.inf
        for idx, move in enumerate(legal_moves):
            board.push(move)
            if depth >= 3 and idx > 3 and not board.is_capture(move) and not board.is_check():
                reduction = 2 if idx > 8 else 1
                evaluation, _ = pvs_search(board, depth - 1 - reduction, alpha, beta)
            else:
                evaluation = beta - 1

            if not b_search_pv:
                evaluation, _ = pvs_search(board, depth - 1, beta - 1, beta)
                if alpha < evaluation < beta:
                    evaluation, _ = pvs_search(board, depth - 1, alpha, beta)
            else:
                if evaluation == beta - 1:
                    evaluation, _ = pvs_search(board, depth - 1, alpha, beta)
                
            board.pop()
            if abort_search: return beta, best_move
            
            if evaluation < min_eval:
                min_eval = evaluation
                best_move = move
            beta = min(beta, evaluation)
            if beta <= alpha: break
            b_search_pv = False
            
        if not abort_search:
            flag = 0 if alpha < min_eval < beta else (1 if min_eval <= alpha else 2)
            transposition_table[board_hash] = (depth, flag, min_eval, best_move)
        return min_eval, best_move

# ==========================================
# 3. INTERACTIVE MAIN APPLICATION SUITE
# ==========================================

class MasterChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Grandmaster Chess Suite")
        self.root.geometry("740x620")  # Widened layout to comfortably seat sidebar
        self.root.configure(bg="#1e1e1e")
        self.root.resizable(False, False)
        
        self.board = None
        self.selected_square = None
        self.hint_squares = []
        self.tournament_mode = False
        
        self.show_launcher_menu()

    def show_launcher_menu(self):
        self.launcher_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.launcher_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        title = tk.Label(self.launcher_frame, text="CHOOSE YOUR ENGINE MODE", fg="#FFFFFF", bg="#1e1e1e", font=("Helvetica", 16, "bold"))
        title.pack(pady=20)
        
        btn_style = {"font": ("Helvetica", 12, "bold"), "fg": "#FFFFFF", "relief": "flat", "width": 25, "pady": 8}
        tk.Button(self.launcher_frame, text="Three-Check Variant Engine", command=lambda: self.launch_engine("3check"), bg="#cf6a4c", **btn_style).pack(pady=10)
        tk.Button(self.launcher_frame, text="Chess960 Elite Engine", command=lambda: self.launch_engine("960"), bg="#4a7a96", **btn_style).pack(pady=10)
        tk.Button(self.launcher_frame, text="CheetahChess Engine (Hyper Fast)", command=lambda: self.launch_engine("cheetah"), bg="#769656", **btn_style).pack(pady=10)

    def launch_engine(self, mode):
        global current_mode
        current_mode = mode
        self.launcher_frame.destroy()
        
        if mode == "3check":
            self.board = chess.variant.ThreeCheckBoard()
            theme_color = "#cf6a4c"
        elif mode == "960":
            self.board = chess.Board(chess960=True)
            self.board.set_chess960_pos(random.randint(0, 959))
            theme_color = "#4a7a96"
        else:
            self.board = chess.Board()
            theme_color = "#769656"

        self.setup_game_ui(theme_color)
        self.apply_elo_difficulty()
        self.render_board_state()

    def setup_game_ui(self, theme_color):
        # Top Scoreboard Bar
        self.top_panel = tk.Frame(self.root, bg="#1e1e1e", pady=10)
        self.top_panel.pack(fill="x")
        self.status_label = tk.Label(self.top_panel, text="White to move", fg="#FFFFFF", bg="#1e1e1e", font=("Helvetica", 12, "bold"))
        self.status_label.pack()

        # Layout Split: Left Main Playing Canvas
        self.canvas = tk.Canvas(self.root, width=480, height=480, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side="left", padx=15)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Layout Split: Right Sidebar Control Command Center
        self.sidebar = tk.Frame(self.root, bg="#262522", width=200, height=480)
        self.sidebar.pack(side="right", fill="y", padx=10, pady=5)
        self.sidebar.pack_propagate(False)

        # Elo Adjuster Dropdown Component
        elo_label = tk.Label(self.sidebar, text="Adjust Bot Difficulty:", fg="#FFFFFF", bg="#262522", font=("Helvetica", 10, "bold"))
        elo_label.pack(pady=(15, 2))
        
        self.elo_var = tk.StringVar(value="2700 (Grandmaster)")
        self.elo_dropdown = tk.OptionMenu(self.sidebar, self.elo_var, "1200 (Easy)", "1600 (Medium)", "2000 (Expert)", "2700 (Grandmaster)", command=self.on_elo_change)
        self.elo_dropdown.config(bg="#1e1e1e", fg="#FFFFFF", relief="flat", font=("Helvetica", 9))
        self.elo_dropdown.pack(fill="x", padx=10, pady=5)

        # Functional Buttons Side Grid
        side_btn = {"font": ("Helvetica", 10, "bold"), "fg": "#FFFFFF", "relief": "flat", "pady": 6}
        tk.Button(self.sidebar, text="💡 Get Move Hint", command=self.trigger_hint, bg="#3b3a36", **side_btn).pack(fill="x", padx=10, pady=5)
        tk.Button(self.sidebar, text="↩️ Undo Last Move", command=self.trigger_undo, bg="#3b3a36", **side_btn).pack(fill="x", padx=10, pady=5)
        
        self.tourney_btn = tk.Button(self.sidebar, text="⚔️ AI vs AI Tourney", command=self.toggle_tournament, bg="#b38f00", **side_btn)
        self.tourney_btn.pack(fill="x", padx=10, pady=5)
        
        tk.Button(self.sidebar, text="🏠 Main Menu", command=self.return_to_menu, bg=theme_color, **side_btn).pack(fill="x", padx=10, pady=(40, 5))

    def apply_elo_difficulty(self):
        global chosen_elo, time_limit
        selection = self.elo_var.get()
        chosen_elo = int(selection.split()[0])
        
        # Adjust calculation boundaries dynamically based on ELO settings
        if chosen_elo == 1200:   self.max_target_depth, time_limit = 2, 0.05
        elif chosen_elo == 1600: self.max_target_depth, time_limit = 4, 0.20
        elif chosen_elo == 2000: self.max_target_depth, time_limit = 8, 0.80
        else:                     self.max_target_depth, time_limit = 32, 2.5

    def on_elo_change(self, event):
        self.apply_elo_difficulty()

    def trigger_hint(self):
        if self.board.is_game_over() or self.board.turn == chess.BLACK: return
        global start_time, abort_search
        start_time = time.time()
        abort_search = False
        # Fast shallow evaluation to uncover instant tactical hints
        _, hint_move = pvs_search(self.board, 4, -math.inf, math.inf)
        if hint_move:
            self.hint_squares = [hint_move.from_square, hint_move.to_square]
            self.render_board_state()

    def trigger_undo(self):
        # Safely remove one full pair of turns (yours and the bot's response)
        if len(self.board.move_stack) >= 2:
            self.board.pop()
            self.board.pop()
            self.hint_squares = []
            self.render_board_state()

    def toggle_tournament(self):
        self.tournament_mode = not self.tournament_mode
        if self.tournament_mode:
            self.tourney_btn.config(bg="#cc0000", text="⏹️ Stop Tourney")
            self.trigger_engine_turn()
        else:
            self.tourney_btn.config(bg="#b38f00", text="⚔️ AI vs AI Tourney")

    def render_board_state(self):
        self.canvas.delete("all")
        if current_mode == "3check": colors = ["#EADECA", "#cf6a4c"]
        elif current_mode == "960": colors = ["#EADECA", "#4a7a96"]
        else: colors = ["#EEEED2", "#769656"]
        
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                color = colors[(rank + file) % 2]
                
                if self.selected_square == square:
                    color = "#BAC466"
                elif square in self.hint_squares:
                    color = "#ffcc00" if square == self.hint_squares[0] else "#ffe680"
                    
                x1, y1 = file * 60, rank * 60
                x2, y2 = x1 + 60, y1 + 60
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                piece = self.board.piece_at(square)
                if piece:
                    unicode_symbol = piece.unicode_symbol()
                    text_color = "#000000" if piece.color == chess.WHITE else "#1e1e1e"
                    self.canvas.create_text(x1 + 30, y1 + 30, text=unicode_symbol, font=("Arial", 36), fill=text_color)

        w_str = "White" if self.board.turn == chess.WHITE else "Black"
        thinking_str = " (Thinking...)" if (self.board.turn == chess.BLACK or self.tournament_mode) else ""
        
        if current_mode == "3check":
            w_checks = 3 - self.board.remaining_checks[chess.BLACK]
            b_checks = 3 - self.board.remaining_checks[chess.WHITE]
            self.status_label.config(text=f"{w_str}{thinking_str} to move | Checks W: {w_checks}/3 | B: {b_checks}/3")
        elif current_mode == "960":
            self.status_label.config(text=f"{w_str}{thinking_str} to move | Chess960 Position Index: {self.board.chess960_pos()}")
        else:
            self.status_label.config(text=f"{w_str}{thinking_str} to move | Cheetah Mode active")

    def on_canvas_click(self, event):
        if self.board.is_game_over() or self.board.turn == chess.BLACK or self.tournament_mode:
            return

        file = event.x // 60
        rank = 7 - (event.y // 60)
        clicked_square = chess.square(file, rank)
        self.hint_squares = [] # Wipe older hint overlays on click

        if self.selected_square is None:
            piece = self.board.piece_at(clicked_square)
            if piece and piece.color == chess.WHITE:
                self.selected_square = clicked_square
                self.render_board_state()
        else:
            move = None
            for legal_move in self.board.legal_moves:
                if legal_move.from_square == self.selected_square and legal_move.to_square == clicked_square:
                    move = legal_move
                    break
            if not move:
                move = chess.Move(self.selected_square, clicked_square)
                if self.board.piece_at(self.selected_square) and self.board.piece_at(self.selected_square).piece_type == chess.PAWN:
                    if chess.square_rank(clicked_square) == 7: move.promotion = chess.QUEEN

            if move in self.board.legal_moves:
                self.board.push(move)
                self.selected_square = None
                self.render_board_state()
                if not self.check_game_termination():
                    self.root.after(50, self.trigger_engine_turn)
            else:
                piece = self.board.piece_at(clicked_square)
                if piece and piece.color == chess.WHITE: self.selected_square = clicked_square
                else: self.selected_square = None
                self.render_board_state()

    def trigger_engine_turn(self):
        if self.board.is_game_over(): return
            
        global start_time, abort_search
        start_time = time.time()
        abort_search = False
        absolute_best_move = None
        last_eval = 0
        
        for current_depth in range(1, self.max_target_depth + 1):
            if current_depth >= 5:
                alpha = last_eval - 40
                beta = last_eval + 40
                eval_score, engine_move = pvs_search(self.board, current_depth, alpha, beta)
                if eval_score <= alpha or eval_score >= beta:
                    eval_score, engine_move = pvs_search(self.board, current_depth, -math.inf, math.inf)
            else:
                eval_score, engine_move = pvs_search(self.board, current_depth, -math.inf, math.inf)
            
            if not abort_search and engine_move:
                absolute_best_move = engine_move
                last_eval = eval_score
            else:
                break
        
        if not absolute_best_move and list(self.board.legal_moves):
            absolute_best_move = list(self.board.legal_moves)
            
        if absolute_best_move:
            self.board.push(absolute_best_move)
            
        self.render_board_state()
        
        if not self.check_game_termination() and self.tournament_mode:
            # Loop next turn schedules for infinite self play cycles
            self.root.after(100, self.trigger_engine_turn)

    def check_game_termination(self) -> bool:
        if self.board.is_game_over():
            self.tournament_mode = False
            outcome = self.board.outcome()
            msg = "Game Over! "
            if outcome.winner == chess.WHITE: msg += "White Victory!"
            elif outcome.winner == chess.BLACK: msg += "Black Victory!"
            else: msg += "It's a draw."
            messagebox.showinfo("Match Finished", f"{msg}\nReason: {outcome.termination.name}")
            return True
        return False

    def return_to_menu(self):
        self.tournament_mode = False
        self.top_panel.destroy()
        self.canvas.destroy()
        self.sidebar.destroy()
        global transposition_table
        transposition_table.clear()
        self.show_launcher_menu()

if __name__ == "__main__":
    window = tk.Tk()
    
    # Safety wrapper: if the icon file cannot be found, ignore it and load the game anyway!
    try:
        app_icon = tk.PhotoImage(file="CHESS ICON.png") 
        window.iconphoto(False, app_icon)
    except Exception:
        pass  # Prevents the "Unhandled Exception" crash if the image path is broken
        
    app = MasterChessApp(window)
    window.mainloop()

