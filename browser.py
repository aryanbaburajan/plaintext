import tkinter
import tkinter.font
import html
import time
import copy
from url import *


HSTEP = 13
VSTEP = 18

FONTS = {}


def get_font(size, weight, slant):
    key = (size, weight, slant)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
                                 slant=slant)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("plaintext browser")
        self.socket_cache = SocketCache()
        self.scroll_x = 0
        self.scroll_y = 0
        self.scroll_step = VSTEP * 4
        self.width = 800
        self.height = 600
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.configure(background='white')
        self.window.bind("<Configure>", self.configure_handle)
        self.window.bind("<Up>", self.scroll_up)
        self.window.bind("<Button-4>", self.scroll_up)
        self.window.bind("<Home>", self.top)
        self.window.bind("<Down>", self.scroll_down)
        self.window.bind("<Button-5>", self.scroll_down)
        self.window.bind("<End>", self.bottom)
        self.configure_handling_flag = False

    def load(self, url):
        url = URL(url, self.socket_cache)
        body = url.request()
        self.tokens = self.lex(body)

        self.layout()
        self.draw()

    def lex(self, body):
        out = []
        buffer = ""
        in_tag = False
        for c in body:
            if c == "<":
                in_tag = True
                if buffer:
                    out.append(Text(buffer))
                buffer = ""
            elif c == ">":
                in_tag = False
                out.append(Tag(buffer))
                buffer = ""
            else:
                buffer += c
        if not in_tag and buffer:
            out.append(Text(buffer))
        return out

    def layout(self):
        self.display_list = Layout(self.tokens, width=self.width).display_list
        self.document_height = max(self.display_list, key=lambda x: x[1])[
            1] if len(self.display_list) != 0 else 1

    def draw(self):
        self.canvas.delete("all")
        self.draw_content()
        self.draw_scrollbar()

    def draw_content(self):
        for x, y, word, font in self.display_list:
            if y > self.scroll_y + self.height:
                continue
            if y + VSTEP < self.scroll_y:
                continue
            self.canvas.create_text(
                x - self.scroll_x, y - self.scroll_y, text=word, font=font, anchor="nw")

    def draw_scrollbar(self):
        if self.height / self.document_height >= 1:
            return

        padding = 5
        scrollbar_width = 10
        scrollbar_height = int(
            (self.height - padding * 2) * self.height / self.document_height)

        scrollbar_y = padding + (self.height - padding * 2) * \
            self.scroll_y / self.document_height
        self.canvas.create_rectangle(
            self.width - scrollbar_width - padding, scrollbar_y, self.width - padding, scrollbar_height + scrollbar_y, fill="black")

    def close(self):
        self.socket_cache.close_sockets()

    def configure_handle(self, e):
        self.configure_event = e
        self.configure()

        # if not self.configure_handling_flag:
        #     self.configure_handling_flag = True
        #     self.canvas.after(100, self.configure)

    def configure(self):
        self.width = self.configure_event.width
        self.height = self.configure_event.height
        self.layout()
        self.draw()
        # self.configure_handling_flag = False

    def update_scroll(self):
        self.scroll_y = max(self.scroll_y, 0)
        self.scroll_x = max(self.scroll_x, 0)
        self.scroll_y = min(self.scroll_y, max(
            self.document_height - self.height, 0))
        self.scroll_x = min(self.scroll_x, 0)
        self.draw()

    def scroll_down(self, e):
        self.scroll_y += self.scroll_step
        self.update_scroll()

    def scroll_up(self, e):
        self.scroll_y -= self.scroll_step
        self.update_scroll()

    def top(self, e):
        self.scroll_y = 0
        self.update_scroll()

    def bottom(self, e):
        self.scroll_y = self.document_height
        self.update_scroll()


class Layout:
    def __init__(self, tokens, width):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.width = width
        self.line = []
        self.size = 12
        self.weight = "normal"
        self.style = "roman"
        self.align = "left"

        for token in tokens:
            self.token(token)

        self.flush()

    def token(self, token):
        if isinstance(token, Text):
            for word in token.text.split():
                self.word(word)
        elif isinstance(token, Tag):
            match token.tag:
                case "i":
                    self.style = "italic"
                case "/i":
                    self.style = "roman"
                case "b":
                    self.weight = "bold"
                case "/b":
                    self.weight = "normal"
                case "small":
                    self.size -= 2
                case "/small":
                    self.size += 2
                case "big":
                    self.size += 4
                case "/big":
                    self.size -= 4
                case "/p":
                    self.flush()
                    self.cursor_y += VSTEP
                case 'h1 class="title"':
                    self.align = "center"
                    self.size += 6
                    self.weight = "bold"
                case '/h1':
                    self.size -= 6
                    self.weight = "normal"
                    self.flush()
                    self.cursor_y += VSTEP
                    self.align = "left"
                case _:
                    if token.tag.startswith("/"):
                        self.flush()
                        self.cursor_y += VSTEP

    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        if word != "\n":
            w = font.measure(word)

            if self.cursor_x + w > self.width - HSTEP:
                self.flush()

            self.line.append((self.cursor_x, word, font))
            self.cursor_x += w + font.measure(" ")
        else:
            self.cursor_y += font.metrics("linespace") * 1.25
            self.cursor_x = HSTEP

    def flush(self):
        if not self.line:
            return

        # x
        line_width, _, _ = self.line[-1]
        if self.align == "center":
            anchor_x = self.width / 2 - 3 * line_width / 4
            for i, (x, word, font) in enumerate(self.line):
                x += anchor_x
                self.line[i] = (x, word, font)

        # y
        metrics = [font.metrics() for _, _, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent
        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))
            max_descent = max([metric["descent"] for metric in metrics])
            self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []
