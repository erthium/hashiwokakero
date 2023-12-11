# [x] TODO: InputBox should be refactored 
# [] TODO: InputBox find_next_word_index should be fixed according to the common sense with DELETE key
# [] TODO: For all elements that are rendering more than 1 element, the sub/child elements should be rendered
# on the parent surface but not the root surface, and parent and child surfaces should be updated only when
# a factor that effects the render output changes inside the child or parent element
# [] TODO: More elements should be added -> CheckBox, ToggleButton, Slider, Image, RadioButton, DropDown List, ListBox etc.
# [] TODO: Sub-elements for increasing the usability of other elements: Slider, ScrollBar, ToolTip,
# ProgressBar ProgressRing, MessageBox service etc.
# [] TODO: Navigational Elements: Layout, Grid, Tab, Menu, MenuBar, ToolBar, StatusBar, TreeView, ListView etc.
# [] TODO: All interactables - button, checkbox, toggle button etc - should be inherited from the InteractableElement class
# [] TODO: InputBox with multiline support 
	# Main issues are: Cursor position, adding new lines and going to the next line when the word is too long
# [] TODO: Hotkeys could be added and bound to interactable elements

import pygame
from pygame import Surface
from pygame.rect import Rect
from enum import Enum
from time import time as get_time
import re, os

ABS_DIR = os.path.dirname(os.path.abspath(__file__))

EMPTY_FUNCTION = lambda: 0
DEFAULT_FONT_PATH = ABS_DIR + '/data/SpaceMono-Regular.ttf'
VALID_INPUT_CHARACTERS = r"[^a-zA-Z0-9., &%+-=^$'\"()\[\]{}*?!@#_/\\|:;<>~`]"
INPUTBOX_TEXT_SIDE_MARGIN = 5
INPUTBOX_HOVERING_CURSOR = pygame.SYSTEM_CURSOR_IBEAM
INPUTBOX_CURSOR_BLINK_INTERVAL = 0.6 # In seconds

_DEPRECATED_VALID_INPUT_CHARACTERS = r'[^\.A-Za-z0-9 _]'
_DEPRECATED_INPUTBOX_CURSOR_CHARACTER = "|"

class InterfaceStatus(Enum):
	VISIBLE = 0
	VISIBLE_UNINTERACTABLE = 1
	INVISIBLE = 2


class Alignment(Enum):
	LEFT_TOP = 0
	TOP = 1
	RIGHT_TOP = 2
	LEFT = 3
	CENTER = 4
	RIGHT = 5
	LEFT_BOTTOM = 6
	BOTTOM = 7
	RIGHT_BOTTOM = 8


class InterfaceElement:
	"""
	Do not change rect properties directy, use move_to() and resize() methods instead
	"""
	def __init__(self, root_surface:Surface, 
			  	status:InterfaceStatus = InterfaceStatus.VISIBLE, 
			  	x:int = 0, y:int = 0, width:int = 0, height:int = 0, 
				alignment:Alignment = Alignment.LEFT_TOP,
				parent = None):
		self.root_surface: Surface = root_surface
		self.rect: Rect = Rect(x, y, width, height)
		self.status: InterfaceStatus = status
		self._alignment: Alignment = alignment
		self._parent: InterfaceElement = parent
		self.children: list = []
		self.should_update = False
		AlignRect(self)
	
	@property
	def parent(self):
		"""Parent element of the current element, returns an InterfaceElement object"""
		return self._parent

	@parent.setter
	def parent(self, new_parent) -> None:
		# TODO: Type check will be added when the system is ready
		# assert isinstance(new_parent, InterfaceElement) or issubclass(type(new_parent), InterfaceElement)
		self._parent = new_parent
		self.root_surface = new_parent.root_surface

	def add_child(self, child) -> None:
		# TODO: Type check will be added when the system is ready
		# assert isinstance(new_parent, InterfaceElement) or issubclass(type(new_parent), InterfaceElement)
		self.children.append(child)
		self.should_update = True

	def add_children(self, children:list) -> None:
		self.children.extend(children)
		self.should_update = True

	def trigger_update(self) -> None:
		self.should_update = True
		if self.parent:
			self.parent.trigger_update()

	def change_status(self, new_status) -> None:
		assert new_status in InterfaceStatus
		self.status = new_status

	@property
	def alignment(self) -> Alignment:
		return self._alignment

	@alignment.setter
	def alignment(self, new_alignment) -> None:
		self._alignment = new_alignment
		AlignRect(self)
		self.should_update = True
	
	def move_to(self, x, y) -> None:
		self.rect.x = x
		self.rect.y = y
		AlignRect(self)
		self.trigger_update()
	
	def resize(self, width, height) -> None:
		self.rect.width = width
		self.rect.height = height
		AlignRect(self)
		self.trigger_update()

	def update(self) -> None:
		for child in self.children:
			child.update()
			child.render()

	def render(self) -> None:
		if self.status == InterfaceStatus.INVISIBLE: return
		if self.should_update:
			self.update()
			self.should_update = False
		self.root_surface.blit(self.surface, (self.rect.x, self.rect.y))


def AlignRect(element:InterfaceElement) -> None:
	"""
	Alignes the Rect of the element according to the alignment with the current x and y of the rect
	"""
	if element.alignment == Alignment.LEFT_TOP:
		element.rect.left = element.rect.x
		element.rect.top = element.rect.y
	elif element.alignment == Alignment.TOP:
		element.rect.centerx = element.rect.x
		element.rect.top = element.rect.y
	elif element.alignment == Alignment.RIGHT_TOP:
		element.rect.right = element.rect.x
		element.rect.top = element.rect.y
	elif element.alignment == Alignment.LEFT:
		element.rect.left = element.rect.x
		element.rect.centery = element.rect.y
	elif element.alignment == Alignment.CENTER:
		element.rect.centerx = element.rect.x
		element.rect.centery = element.rect.y
	elif element.alignment == Alignment.RIGHT:
		element.rect.right = element.rect.x
		element.rect.centery = element.rect.y
	elif element.alignment == Alignment.LEFT_BOTTOM:
		element.rect.left = element.rect.x
		element.rect.bottom = element.rect.y
	elif element.alignment == Alignment.BOTTOM:
		element.rect.centerx = element.rect.x
		element.rect.bottom = element.rect.y
	elif element.alignment == Alignment.RIGHT_BOTTOM:
		element.rect.right = element.rect.x
		element.rect.bottom = element.rect.y


def ElementCollide(element:InterfaceElement, mouse_position) -> bool:
	"""
	Checks if the mouse is colliding with the button
	"""
	return element.rect.collidepoint(mouse_position)


class Canvas(InterfaceElement):
	"""
	Empty element to be used as a container and a parent for other elements.
	It's important to have a 1 parent for all elements, to increase performance.
	Canvas element does not have any background, it has an empty surface to blit other elements on it.
	Ideally there should be only 1 canvas element in a scene.
	"""
	def __init__(self, root_surface: Surface, status: InterfaceStatus = InterfaceStatus.VISIBLE, 
			  	x: int = 0, y: int = 0, width: int = 0, height: int = 0, 
				alignment: Alignment = Alignment.LEFT_TOP, parent=None):
		super().__init__(root_surface, status, x, y, width, height, alignment, parent)
		self.surface: Surface = Surface((width, height))


class Text(InterfaceElement):
	def __init__(self, root_surface, x:int = 0, y:int = 0,  
			  	text:str = "New Text", font_size:int = 11, color:tuple = (0,0,0), 
				alignment:Alignment = Alignment.LEFT_TOP,
				status:int = InterfaceStatus.VISIBLE):
		self.surface = None
		self.text:str = text
		self.color:tuple = color
		self.font_size = font_size
		self.font:pygame.font.Font = pygame.font.Font(DEFAULT_FONT_PATH, font_size)
		self.surface:Surface = self.font.render(self.text, True, color)
		InterfaceElement.__init__(self, root_surface, status, x, y, 
								self.surface.get_width(), 
								self.surface.get_height(), alignment)

	def change_text_to(self, new_text:str, font_size:int = None):
		if font_size is int and font_size > 0 and self.font_size != font_size:
			self.font_size = font_size
			self.font = pygame.font.Font(DEFAULT_FONT_PATH, font_size)
		self.text = new_text
		self.surface = self.font.render(self.text, True, self.color)

	def change_color_to(self, new_color:tuple):
		assert new_color[0] is int and new_color[1] is int and new_color[2] is int
		self.color = new_color
		self.surface = self.font.render(self.text, True, new_color)

	def render(self):
		if self.status == InterfaceStatus.INVISIBLE: return
		self.root_surface.blit(self.surface, (self.rect.x, self.rect.y))


class InteractablePhase(Enum):
	DEFAULT = 0
	HOVER = 1
	PRESSED = 2

#class InteractableElement(InterfaceElement):
#	pass

class Button(InterfaceElement):
	def __init__(self, root_surface, x: int = 0, y: int = 0, width: int = 100, height: int = 25, 
			  	click_function: callable=EMPTY_FUNCTION, args: tuple = tuple(), kwargs: dict = {}, 
				text="Button", font_size=11,
				background: tuple = (190,190,190), foreground: tuple = (0,0,0),
				border_color: tuple = (0,0,0), border_width: int = 4,
				status: InterfaceStatus = InterfaceStatus.VISIBLE,
				alignment: Alignment = Alignment.LEFT_TOP,
				hover_color: tuple = (0,0,0,50), pressed_color: tuple = (0,0,0,150),
				hover_event: callable = EMPTY_FUNCTION, hover_args:tuple = tuple(), hover_kwargs:dict = {},
				pressed_event: callable = EMPTY_FUNCTION, pressed_args:tuple = tuple(), pressed_kwargs:dict = {}):
		self.surface: Surface = Surface((width, height))
		self.surface.fill(background)
		pygame.draw.rect(self.surface, border_color, (0, 0, width, height), border_width)

		self.phase: InteractablePhase = InteractablePhase.DEFAULT
		self.effect_surface: Surface = Surface((width, height), pygame.SRCALPHA).convert_alpha()
		self.hover_color: tuple = hover_color
		self.pressed_color: tuple = pressed_color

		# Events
		self.hover_event: callable = hover_event
		self.hover_args: tuple = hover_args
		self.hover_kwargs: dict = hover_kwargs

		self.pressed_event: callable = pressed_event
		self.pressed_args: tuple = pressed_args
		self.pressed_kwargs: dict = pressed_kwargs

		self.click_function: callable = click_function
		self.args: tuple = args
		self.kwargs: dict = kwargs

		InterfaceElement.__init__(self, root_surface, status, x, y, 
								width, height, alignment)
		self.text:Text = Text(root_surface, self.rect.centerx, self.rect.centery, text, 
							font_size, foreground, Alignment.CENTER)

	def hover(self):
		self.phase = InteractablePhase.HOVER
		self.hover_event(*self.hover_args, **self.hover_kwargs)
	
	def press(self):
		self.phase = InteractablePhase.PRESSED
		self.pressed_event(*self.pressed_args, **self.pressed_kwargs)

	def click(self):
		self.click_function(*self.args, **self.kwargs)
		self.phase = InteractablePhase.HOVER

	def render(self):
		if self.status == InterfaceStatus.INVISIBLE: return

		self.root_surface.blit(self.surface, (self.rect.x, self.rect.y))
		self.text.render()

		if self.phase == InteractablePhase.DEFAULT: return
		if self.phase == InteractablePhase.HOVER:
			self.effect_surface.fill(self.hover_color)
		elif self.phase == InteractablePhase.PRESSED:
			self.effect_surface.fill(self.pressed_color)
		self.root_surface.blit(self.effect_surface, (self.rect.x, self.rect.y))


class InputBox(InterfaceElement):
	def __init__(self, root_surface, x: int = 0, y: int = 0, width: int = 100, height: int = 25, 
				font_size: int = 11, background: tuple = (190, 190, 190), 
				foreground:tuple = (0, 0, 0), border_color: tuple = (0, 0, 0), 
				border_width: int = 4, status: InterfaceStatus = InterfaceStatus.VISIBLE,
				alignment: Alignment = Alignment.LEFT_TOP, 
				place_holder_text: str = "Enter Text...", place_holder_color: tuple = (80, 80, 80)):
		self.surface: Surface = Surface((width, height))
		self.surface.fill(background)
		pygame.draw.rect(self.surface, border_color, (0, 0, width, height), border_width)

		self._selected: bool = False
		self._cursor: int = 0 # Character index of the current cursor position
		self.cursor_position_x: int = 0
		self.last_blink_time: int = 0
		self.is_blinking : bool = False

		InterfaceElement.__init__(self, root_surface, status, x, y, 
								width, height, alignment)
		self.place_holder: Text = Text(root_surface, self.rect.left + INPUTBOX_TEXT_SIDE_MARGIN, self.rect.centery, place_holder_text, 
									font_size, place_holder_color, Alignment.LEFT)
		self.text: Text = Text(root_surface, self.rect.left + INPUTBOX_TEXT_SIDE_MARGIN, self.rect.centery, str(), 
									font_size, foreground, Alignment.LEFT)
		self.text_char_size: tuple = self.text.font.size("E")
	@property
	def selected(self):
		return self._selected

	@selected.setter
	def selected(self, new_selected):
		self._selected = new_selected
		if new_selected == True:
			self.last_blink_time = get_time()
	
	@property
	def cursor(self):
		return self._cursor

	@cursor.setter
	def cursor(self, new_cursor):
		if new_cursor < 0:
			new_cursor = 0
		elif new_cursor > len(self.text.text):
			new_cursor = len(self.text.text)
		if self._cursor == new_cursor: return

		change = new_cursor - self._cursor
		self._cursor = new_cursor
		self.cursor_position_x += change * self.text_char_size[0]
		self.last_blink_time = get_time()
		self.is_blinking = True


	def add(self, char):
		if re.search(VALID_INPUT_CHARACTERS, char) or len(char) != 1:
			return
		new_text = self.text.text + char
		if(self.text.font.size(new_text)[0] > self.rect.width - INPUTBOX_TEXT_SIDE_MARGIN*2): # 5 pixel margin from each side
			return
		# add the new character to the cursor position
		self.text.change_text_to(self.text.text[:self.cursor] + char + self.text.text[self.cursor:])
		self.cursor += 1

	def remove(self, direction: int = 1):
		# Direction specifies the character removing direction
		# if DELETE key is pressed, direction is -1, if BACKSPACE key is pressed, direction is 1
		# This will be used when cursor is added
		# TO DEVS: It's important to note when DELETE key is pressed, the cursor does not move
		if len(self.text.text) > 0:
			if direction > 0:
				self.text.change_text_to(self.text.text[:self.cursor - 1] + self.text.text[self.cursor:])
				self.cursor -= 1 * direction
			else:
				self.text.change_text_to(self.text.text[:self.cursor] + self.text.text[self.cursor + 1:])

	def find_beginning_of_word(self, direction: int = 1) -> int:
		word_index = self.cursor - 1 * direction
		is_any_char_found = False
		while word_index > 0 and word_index < len(self.text.text):
			current_character = self.text.text[word_index]
			if current_character != " ": is_any_char_found = True
			if current_character == " " and is_any_char_found: break
			word_index -= 1 * direction
		if direction < 0:
			word_index += 1
		return word_index


	def find_word_index(self, direction: int = 1) -> int:
		is_word_found = False
		word_index = self.cursor - 1 * direction
		while word_index > 0 and word_index < len(self.text.text):
			current_character = self.text.text[word_index]
			if current_character != " ": 
				is_word_found = True
			word_index -= 1 * direction
			if word_index < 0 or word_index >= len(self.text.text):
				word_index += 1 * direction
				break
			current_character = self.text.text[word_index]
			if current_character == " " and is_word_found:
				word_index += 1 * direction
				break
		if direction < 0:
			word_index += 1
		return word_index

	def remove_word(self, direction: int = 1):
		removing_index = self.find_beginning_of_word(direction)
		if direction > 0:
			self.text.change_text_to(self.text.text[:removing_index] + self.text.text[self.cursor:])
			self.cursor = removing_index
		else:
			self.text.change_text_to(self.text.text[:self.cursor] + self.text.text[removing_index:])

	def clear(self):
		self.text.change_text_to(str())
		self.cursor = 0

	def render(self):
		if self.status == InterfaceStatus.INVISIBLE: return
		self.root_surface.blit(self.surface, (self.rect.x, self.rect.y))
		if len(self.text.text) > 0:
			self.text.render()
		elif not self.selected:
			self.place_holder.render()
		if self.selected and self.is_blinking:
			line_beginning_position = (self.text.rect.left + self.cursor_position_x, self.text.rect.bottom)
			line_ending_position = (self.text.rect.left + self.cursor_position_x, self.text.rect.bottom - self.text_char_size[1])
			pygame.draw.line(self.root_surface, self.text.color, line_beginning_position, line_ending_position, 1)
		if get_time() - self.last_blink_time > INPUTBOX_CURSOR_BLINK_INTERVAL:
			self.last_blink_time = get_time()
			self.is_blinking = not self.is_blinking


def ProcessElements(events, pressed_keys, mouse_pos, elements:list = [], inputs:list = [], texts:list = []):
	for element_ in elements:
		if ElementCollide(element_, mouse_pos):
			if element_.phase != InteractablePhase.PRESSED:
				element_.hover()
		else:
			element_.phase = InteractablePhase.DEFAULT
	
	for event in events:
		if event.type == pygame.MOUSEBUTTONDOWN:
			for element_ in elements:
				if element_.phase == InteractablePhase.HOVER and element_.status == InterfaceStatus.VISIBLE:
					element_.press()

		elif event.type == pygame.MOUSEBUTTONUP:
			for element_ in elements:
				if element_.phase == InteractablePhase.PRESSED and element_.status == InterfaceStatus.VISIBLE:
					element_.click()
			for input_box in inputs:
				if ElementCollide(input_box, mouse_pos):
					input_box.selected = True
				else: 
					input_box.selected = False

		elif event.type == pygame.KEYDOWN:
			for input_box in inputs:
				if input_box.selected:
					if event.key == pygame.K_BACKSPACE:
						if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
							input_box.remove_word(direction = 1)
						else: 
							input_box.remove(direction = 1)
					if event.key == pygame.K_DELETE:
						if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
							input_box.remove_word(direction = -1)
						else: 
							input_box.remove(direction = -1)
					elif event.key == pygame.K_RETURN:
						# TODO: will add ENTER_KEY event in case InputBox is wanted to be attached with an action
						pass
					elif event.key == pygame.K_LEFT:
						if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
							input_box.cursor = input_box.find_beginning_of_word(direction = 1)
						else:
							input_box.cursor -= 1
					elif event.key == pygame.K_RIGHT:
						if pressed_keys[pygame.K_LCTRL] or pressed_keys[pygame.K_RCTRL]:
							input_box.cursor = input_box.find_beginning_of_word(direction = -1)
						else:
							input_box.cursor += 1
					else: 
						input_box.add(event.unicode)
