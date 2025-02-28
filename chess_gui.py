import pygame
import random
import os

# Визначаємо базову директорію проекту (папка Chess)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

piece_letters = {
    "pawn": "p",
    "rook": "r",
    "knight": "n",
    "bishop": "b",
    "queen": "q",
    "king": "k"
}

class ChessPiece:
    def __init__(self, color, piece_type):
        self.color = color
        self.piece_type = piece_type
        self.has_moved = False
        image_path = os.path.join(BASE_DIR, "pieces", f"{color[0]}{piece_letters[piece_type]}.png")
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (80, 80))
            print(f"Завантажено: {image_path} для {color} {piece_type}")
        except FileNotFoundError:
            print(f"Помилка: Не знайдено файл {image_path}. Перевірте папку pieces.")
            self.image = pygame.Surface((80, 80))  # Порожнє зображення як резерв

class ChessBoard:
    def __init__(self):
        self.board = self.initialize_board()
        self.current_turn = "white"
        self.selected = None  # Поточна вибрана фігура
        self.last_move = None
        self.in_check = False  # Додано для відстеження шаху

    def initialize_board(self):
        board = [[None for _ in range(8)] for _ in range(8)]
        for i in range(8):
            board[1][i] = ChessPiece("black", "pawn")
            board[6][i] = ChessPiece("white", "pawn")
        pieces = ["rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"]
        for i in range(8):
            board[0][i] = ChessPiece("black", pieces[i])
            board[7][i] = ChessPiece("white", pieces[i])
        return board

    def is_path_clear(self, start, end):
        start_row, start_col = start
        end_row, end_col = end
        row_step = 0 if end_row == start_row else (1 if end_row > start_row else -1)
        col_step = 0 if end_col == start_col else (1 if end_col > start_col else -1)
        
        row, col = start_row + row_step, start_col + col_step
        while row != end_row or col != end_col:
            if self.board[row][col]:
                return False
            row += row_step
            col += col_step
        return True

    def get_king_position(self, color):
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.piece_type == "king" and piece.color == color:
                    return (row, col)
        print(f"Попередження: Король {color} не знайдений на дошці!")
        return None

    def is_square_attacked(self, pos, attacker_color):
        if pos is None:
            return False  # Якщо позиція короля не знайдена, вважаємо, що вона не атакована
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == attacker_color:
                    if self.is_valid_move((row, col), pos, check_king=False):
                        return True
        return False

    def is_in_check(self, color):
        king_pos = self.get_king_position(color)
        if king_pos is None:
            return False  # Якщо король не знайдений, вважаємо, що немає шаху
        return self.is_square_attacked(king_pos, "black" if color == "white" else "white")

    def is_checkmate(self, color):
        if not self.is_in_check(color):
            return False
        for start_row in range(8):
            for start_col in range(8):
                piece = self.board[start_row][start_col]
                if piece and piece.color == color:
                    for end_row in range(8):
                        for end_col in range(8):
                            if self.is_valid_move((start_row, start_col), (end_row, end_col), check_king=False):
                                # Симулюємо хід
                                original_end = self.board[end_row][end_col]
                                self.board[end_row][end_col] = piece
                                self.board[start_row][start_col] = None
                                still_in_check = self.is_in_check(color)
                                # Відновлюємо дошку
                                self.board[start_row][start_col] = piece
                                self.board[end_row][end_col] = original_end
                                if not still_in_check:
                                    return False
        return True

    def can_move_out_of_check(self, start, end):
        if not self.is_in_check(self.current_turn):
            return True
        start_row, start_col = start
        piece = self.board[start_row][start_col]
        if piece.piece_type != "king":  # Дозволяємо ходити лише королем, якщо в шаху
            return False
        original_end = self.board[end[0]][end[1]]
        self.board[end[0]][end[1]] = piece
        self.board[start_row][start_col] = None
        in_check = self.is_in_check(self.current_turn)
        self.board[start_row][start_col] = piece
        self.board[end[0]][end[1]] = original_end
        return not in_check

    def is_valid_move(self, start, end, check_king=True):
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        
        if not piece or piece.color != self.current_turn:
            return False
            
        target = self.board[end_row][end_col]
        if target and target.color == piece.color:
            return False
            
        row_diff = end_row - start_row
        col_diff = end_col - start_col
        abs_row_diff = abs(row_diff)
        abs_col_diff = abs(col_diff)

        if piece.piece_type == "pawn":
            direction = -1 if piece.color == "white" else 1
            if col_diff == 0 and not target:
                if row_diff == direction:
                    return True
                if row_diff == 2 * direction and not piece.has_moved:
                    return self.board[start_row + direction][start_col] is None
            if abs_col_diff == 1 and row_diff == direction:
                if target:
                    return True
                if (piece.color == "white" and start_row == 3) or \
                   (piece.color == "black" and start_row == 4):
                    if self.last_move and abs(self.last_move[1][1] - self.last_move[0][1]) == 0:
                        last_start, last_end = self.last_move
                        if last_end == (start_row, end_col) and \
                           self.board[last_end[0]][last_end[1]] and \
                           self.board[last_end[0]][last_end[1]].piece_type == "pawn":
                            return True
            return False

        if piece.piece_type == "knight":
            return (abs_row_diff == 2 and abs_col_diff == 1) or \
                   (abs_row_diff == 1 and abs_col_diff == 2)

        if piece.piece_type == "bishop":
            return abs_row_diff == abs_col_diff and self.is_path_clear(start, end)

        if piece.piece_type == "rook":
            return (row_diff == 0 or col_diff == 0) and self.is_path_clear(start, end)

        if piece.piece_type == "queen":
            return ((row_diff == 0 or col_diff == 0) or 
                    (abs_row_diff == abs_col_diff)) and self.is_path_clear(start, end)

        if piece.piece_type == "king":
            if abs_row_diff <= 1 and abs_col_diff <= 1:
                return True
            if not piece.has_moved and row_diff == 0 and abs_col_diff == 2:
                rook_col = 0 if col_diff < 0 else 7
                rook = self.board[start_row][rook_col]
                if rook and rook.piece_type == "rook" and not rook.has_moved:
                    return self.is_path_clear(start, (start_row, rook_col))
            return False

        return False

    def get_possible_moves(self, start):
        possible_moves = []
        start_row, start_col = start
        for end_row in range(8):
            for end_col in range(8):
                if self.is_valid_move(start, (end_row, end_col)) and self.can_move_out_of_check(start, (end_row, end_col)):
                    original_end = self.board[end_row][end_col]
                    piece = self.board[start_row][start_col]
                    self.board[end_row][end_col] = piece
                    self.board[start_row][start_col] = None
                    if not self.is_in_check(piece.color):
                        possible_moves.append((end_row, end_col))
                    self.board[start_row][start_col] = piece
                    self.board[end_row][end_col] = original_end
        return possible_moves

    def make_move(self, start, end):
        if not self.is_valid_move(start, end):
            return False
            
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        
        if piece.piece_type == "pawn" and abs(end_col - start_col) == 1 and not self.board[end_row][end_col]:
            self.board[start_row][end_col] = None

        if piece.piece_type == "king" and abs(end_col - start_col) == 2:
            rook_col = 0 if end_col < start_col else 7
            new_rook_col = 3 if end_col < start_col else 5
            self.board[end_row][new_rook_col] = self.board[start_row][rook_col]
            self.board[start_row][rook_col] = None

        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = None
        piece.has_moved = True
        
        if piece.piece_type == "pawn" and (end_row == 0 or end_row == 7):
            new_piece_type = self.show_promotion_menu(piece.color)
            if new_piece_type:
                piece.piece_type = new_piece_type
                piece.image = pygame.image.load(os.path.join(BASE_DIR, "pieces", f"{piece.color[0]}{piece_letters[new_piece_type]}.png")).convert_alpha()
                piece.image = pygame.transform.scale(piece.image, (80, 80))

        self.last_move = (start, end)
        self.in_check = self.is_in_check(self.current_turn)  # Оновлюємо стан шаху
        
        if self.is_in_check(piece.color):
            self.board[start_row][start_col] = piece
            self.board[end_row][end_col] = None
            if piece.piece_type == "king" and abs(end_col - start_col) == 2:
                self.board[start_row][rook_col] = self.board[end_row][new_rook_col]
                self.board[end_row][new_rook_col] = None
            return False

        self.current_turn = "black" if self.current_turn == "white" else "white"
        return True

    def ai_move(self, difficulty):
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == self.current_turn:
                    moves = self.get_possible_moves((row, col))
                    for move in moves:
                        all_moves.append(((row, col), move))

        if not all_moves:
            return False

        if difficulty == "easy":
            start, end = random.choice(all_moves)
        elif difficulty == "medium":
            capture_moves = [m for m in all_moves if self.board[m[1][0]][m[1][1]]]
            start, end = random.choice(capture_moves if capture_moves else all_moves)
        else:  # hard
            for start_pos, end_pos in all_moves:
                original_end = self.board[end_pos[0]][end_pos[1]]
                piece = self.board[start_pos[0]][start_pos[1]]
                self.board[end_pos[0]][end_pos[1]] = piece
                self.board[start_pos[0]][start_pos[1]] = None
                if self.is_in_check("white" if self.current_turn == "black" else "black"):
                    self.board[start_pos[0]][start_pos[1]] = piece
                    self.board[end_pos[0]][end_pos[1]] = original_end
                    start, end = start_pos, end_pos
                    break
                self.board[start_pos[0]][start_pos[1]] = piece
                self.board[end_pos[0]][end_pos[1]] = original_end
            else:
                start, end = random.choice(all_moves)

        return self.make_move(start, end)

    def show_promotion_menu(self, color):
        pygame.event.clear()  # Очищаємо події, щоб уникнути небажаних кліків
        SQUARE_SIZE = 80
        screen = pygame.display.get_surface()
        font = pygame.font.SysFont("arial", 40)
        
        options = ["queen", "rook", "bishop", "knight"]
        selected_option = options[0]  # По замовчуванню вибрано ферзя
        buttons = {}
        
        while True:
            screen.fill((200, 200, 200))  # Очищаємо екран для оновлення меню
            for i, option in enumerate(options):
                text = font.render(option.capitalize(), True, (0, 0, 0))
                button_rect = text.get_rect(center=(320, 200 + i * 80))
                # Підсвічуємо вибрану опцію іншим кольором
                button_color = (100, 255, 100) if option == selected_option else (100, 100, 100)
                pygame.draw.rect(screen, button_color, (button_rect.left - 20, button_rect.top - 10, 
                                                       button_rect.width + 40, button_rect.height + 20))
                screen.blit(text, button_rect)
                buttons[option] = button_rect

            # Додаємо кнопку підтвердження
            confirm_text = font.render("Підтвердити", True, (0, 0, 0))
            confirm_rect = confirm_text.get_rect(center=(320, 200 + len(options) * 80))
            pygame.draw.rect(screen, (50, 150, 50), (confirm_rect.left - 20, confirm_rect.top - 10, 
                                                    confirm_rect.width + 40, confirm_rect.height + 20))
            screen.blit(confirm_text, confirm_rect)
            buttons["confirm"] = confirm_rect

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    for option, rect in buttons.items():
                        if rect.collidepoint(x, y):
                            if option in options:  # Якщо це одна з фігур
                                selected_option = option
                            elif option == "confirm":  # Підтвердження вибору
                                return selected_option
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        idx = options.index(selected_option)
                        idx = (idx - 1) % len(options)
                        selected_option = options[idx]
                    elif event.key == pygame.K_DOWN:
                        idx = options.index(selected_option)
                        idx = (idx + 1) % len(options)
                        selected_option = options[idx]
                    elif event.key == pygame.K_RETURN:  # Enter для підтвердження
                        return selected_option
                    elif event.key == pygame.K_ESCAPE:  # Escape для відміни виділення
                        return selected_option  # Повертаємо поточний вибір, щоб завершити меню (для сумісності)
                    elif event.key == pygame.K_q:
                        selected_option = "queen"
                    elif event.key == pygame.K_r:
                        selected_option = "rook"
                    elif event.key == pygame.K_b:
                        selected_option = "bishop"
                    elif event.key == pygame.K_n:
                        selected_option = "knight"

def draw_board(screen, game, font):
    SQUARE_SIZE = 80
    screen.fill((255, 255, 255))
    
    # Малюємо дошку, використовуючи рядки від 0 до 7 без інверсії, але коректно відображаючи для гравця
    for row in range(8):  # Змінено: тепер від 0 до 7, щоб верхній ряд (0) був зверху
        for col in range(8):
            # Інвертуємо кольори клітинок для правильного шахового візерунку
            color = (245, 222, 179) if (row + col) % 2 == 0 else (139, 69, 19)
            # Використовуємо row * SQUARE_SIZE для Y, щоб ряд 0 був зверху, а 7 — внизу
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                           SQUARE_SIZE, SQUARE_SIZE))
            piece = game.board[row][col]  # Беремо фігури з внутрішньої дошки без інверсії
            if piece:
                screen.blit(piece.image, (col * SQUARE_SIZE, row * SQUARE_SIZE))

    # Перевірка шаху і виділення короля
    for color in ["white", "black"]:
        king_pos = game.get_king_position(color)
        if king_pos and game.is_in_check(color):
            king_row, king_col = king_pos
            pygame.draw.rect(screen, (255, 0, 0),  # Червона рамка для шаху
                           (king_col * SQUARE_SIZE, king_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

    if game.selected:
        possible_moves = game.get_possible_moves(game.selected)
        for move_row, move_col in possible_moves:
            pygame.draw.circle(screen, (0, 255, 0), 
                             (move_col * SQUARE_SIZE + SQUARE_SIZE//2, 
                              move_row * SQUARE_SIZE + SQUARE_SIZE//2), 
                             10)

    if game.selected:
        row, col = game.selected
        pygame.draw.rect(screen, (255, 255, 0), 
                        (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 3)

def draw_main_menu(screen, font):
    screen.fill((200, 200, 200))
    title = font.render("Шахи", True, (0, 0, 0))
    button_text = font.render("Нова гра", True, (0, 0, 0))
    title_rect = title.get_rect(center=(320, 200))
    button_rect = button_text.get_rect(center=(320, 400))
    pygame.draw.rect(screen, (100, 100, 100), (button_rect.left - 20, button_rect.top - 10, 
                                               button_rect.width + 40, button_rect.height + 20))
    screen.blit(title, title_rect)
    screen.blit(button_text, button_rect)
    return button_rect

def draw_mode_menu(screen, font):
    screen.fill((200, 200, 200))
    vs_player = font.render("Гравець проти Гравця", True, (0, 0, 0))
    vs_ai_easy = font.render("Проти AI (Легкий)", True, (0, 0, 0))
    vs_ai_medium = font.render("Проти AI (Середній)", True, (0, 0, 0))
    vs_ai_hard = font.render("Проти AI (Складний)", True, (0, 0, 0))
    
    vs_player_rect = vs_player.get_rect(center=(320, 200))
    vs_ai_easy_rect = vs_ai_easy.get_rect(center=(320, 300))
    vs_ai_medium_rect = vs_ai_medium.get_rect(center=(320, 400))
    vs_ai_hard_rect = vs_ai_hard.get_rect(center=(320, 500))

    for text, rect in [(vs_player, vs_player_rect), (vs_ai_easy, vs_ai_easy_rect),
                       (vs_ai_medium, vs_ai_medium_rect), (vs_ai_hard, vs_ai_hard_rect)]:
        pygame.draw.rect(screen, (100, 100, 100), (rect.left - 20, rect.top - 10, 
                                                   rect.width + 40, rect.height + 20))
        screen.blit(text, rect)
    
    return {"player": vs_player_rect, "ai_easy": vs_ai_easy_rect, 
            "ai_medium": vs_ai_medium_rect, "ai_hard": vs_ai_hard_rect}

def draw_game_over(screen, font, winner):
    screen.fill((0, 0, 0))  # Чорний фон для екрану гри завершена
    text = font.render(f"Перемогли {winner}!", True, (255, 255, 255))  # Білий текст
    text_rect = text.get_rect(center=(320, 320))
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.wait(2000)  # Показати повідомлення 2 секунди
    # Після показу повідомлення повертаємося до головного меню без подальшого циклу
    return

def play_chess():
    pygame.init()
    SQUARE_SIZE = 80
    WIDTH, HEIGHT = 8 * SQUARE_SIZE, 8 * SQUARE_SIZE
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Шахи")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 40)
    
    state = "main_menu"
    game = None
    vs_ai = False
    ai_difficulty = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if state == "main_menu":
                    button_rect = draw_main_menu(screen, font)
                    if button_rect.collidepoint(x, y):
                        state = "mode_menu"
                elif state == "mode_menu":
                    mode_buttons = draw_mode_menu(screen, font)
                    if mode_buttons["player"].collidepoint(x, y):
                        state = "game"
                        game = ChessBoard()
                        vs_ai = False
                    elif mode_buttons["ai_easy"].collidepoint(x, y):
                        state = "game"
                        game = ChessBoard()
                        vs_ai = True
                        ai_difficulty = "easy"
                    elif mode_buttons["ai_medium"].collidepoint(x, y):
                        state = "game"
                        game = ChessBoard()
                        vs_ai = True
                        ai_difficulty = "medium"
                    elif mode_buttons["ai_hard"].collidepoint(x, y):
                        state = "game"
                        game = ChessBoard()
                        vs_ai = True
                        ai_difficulty = "hard"
                elif state == "game" and (not vs_ai or game.current_turn == "white"):
                    col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
                    if game.selected:
                        if game.make_move(game.selected, (row, col)):
                            game.selected = None
                            if game.is_checkmate("white"):
                                draw_game_over(screen, font, "Чорні")
                                state = "main_menu"
                            elif game.is_checkmate("black"):
                                draw_game_over(screen, font, "Білі")
                                state = "main_menu"
                    else:
                        if game.board[row][col] and game.board[row][col].color == game.current_turn:
                            # Дозволяємо вибирати лише короля, якщо в шаху
                            if game.in_check and game.board[row][col].piece_type != "king":
                                continue
                            game.selected = (row, col)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and state == "game":
                    # Відміняємо виділення, якщо натиснуто Escape
                    game.selected = None

        if state == "main_menu":
            draw_main_menu(screen, font)
        elif state == "mode_menu":
            draw_mode_menu(screen, font)
        elif state == "game":
            draw_board(screen, game, font)
            if vs_ai and game.current_turn == "black":
                if game.ai_move(ai_difficulty):
                    if game.is_checkmate("white"):
                        draw_game_over(screen, font, "Чорні")
                        state = "main_menu"
                    elif game.is_checkmate("black"):
                        draw_game_over(screen, font, "Білі")
                        state = "main_menu"

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    play_chess()