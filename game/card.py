import random
import copy

import pyglet
from pyglet.window import key
from pyglet.window import mouse

from . import util
from . import resources


def cards_equal(card1, card2):
    return card1.operator == card2.operator and card1.value == card2.value and card1.cost == card2.cost


class Card:
    def __init__(self, operator, value, cost):
        self.operator = operator
        self.value = value
        self.cost = cost

    def __eq__(self, obj):
        return cards_equal(self, obj)

    def print(self):
        print("|" + self.operator + str(self.value) + " (" + str(self.cost) + ")|", end="")

    def return_print(self):
        return self.operator + str(self.value) + " (" + str(self.cost) + ")"

    def return_simple_copy(self):
        return Card(operator=self.operator, value=self.value, cost=self.cost)

    def make_negative(self):
        if self.operator == "+":
            self.operator = "-"

    def __eq__(self, other):
        if isinstance(other, Card):
            return cards_equal(self, other)
        return False

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return self.return_print()


class Deck:
    def __init__(self):
        self.stack = []

    def clear(self):
        self.stack = []

    def n_cards(self):
        return len(self.stack)

    def add_card(self, card):
        self.stack.append(card)

    def add_deck(self, deck):
        for card in deck.stack:
            self.add_card(card)

        deck.stack = []

    def shuffle(self):
        random.shuffle(self.stack)

    def draw_card(self, discard):
        if len(self.stack) > 0:
            return self.stack.pop()
        else:
            if discard.n_cards() > 0:
                self.add_deck(discard)
                self.shuffle()
                return self.stack.pop()
            else:
                print("No card left and no discard pile!")

    def draw_hand(self, n_cards, discard):
        cards = []
        for index in range(n_cards):
            cards.append(self.draw_card(discard))

        return cards

    def print(self):
        for card in self.stack:
            card.print()
            print("")

    def make_negative(self):
        for card in self.stack:
            if card.operator == "+":
                card.operator = "-"

    def __repr__(self):
        return f"Deck with {self.n_cards()}"


def get_card_resource(card):
    #print("finding ", card)
    return resources.card_art[(card.operator, card.value, card.cost)]


class ActiveCard(pyglet.sprite.Sprite):

    def __init__(self, *args, **kwargs):

        self.window = kwargs["window"]
        del kwargs["window"]

        self.card = kwargs["card"]
        del kwargs["card"]

        self.cost = self.card.cost
        self.value = self.card.value
        self.operator = self.card.operator

        try:
            imgobj = get_card_resource(self.card)
        except:
            print("failed to load card resource, use back instead")
            imgobj = resources.card_back

        """
        if self.card.filename is None:
            imgobj = resources.card_back
        else:
            imgobj = self.card.resource
        """

        super(ActiveCard, self).__init__(img=imgobj, *args, **kwargs)

        self.x = 100
        self.y = 100


        """
        self.card_label = pyglet.text.Label(text=self.card.return_print(),
                                            x=self.x, y=self.y, batch=kwargs["batch"],
                                            anchor_x='center', anchor_y='center')

        self.card_label = pyglet.text.Label(text=self.card.return_print(),
                                            x=self.x, y=self.y, batch=kwargs["batch"],
                                            anchor_x='center', anchor_y='center')
        """

        self.alt_back = pyglet.sprite.Sprite(img=resources.card_back, *args, **kwargs)
        self.alt_back.scale = 0.1
        self.alt_back.opacity = 0

        self.scale = 0.25
        self.scale_goal = 0.25
        self.scale_speed = 0.15

        self.scale_goal_saved = None

        self.my_speed = 200

        self.target_pos = None
        self.to_stack = False

        self.final_target = False
        self.reached_final_target = False

        self.card_pressed = False

    def return_simple_copy(self):
        return Card(operator=self.operator, value=self.value, cost=self.cost)

    def set_target(self, target):
        self.target_pos = target

    def mouse_position_on_card(self, x, y, button, modifier):
        half_width = self.width / 2
        half_height = self.height / 2
        if self.x + half_width > x > self.x - half_width and self.y + half_height > y > self.y - half_height:

            if modifier & key.MOD_SHIFT:
                if self.scale_goal_saved is None:
                    # not highlighted
                    self.scale_goal_saved = self.scale_goal
                    self.scale_goal = 1.5*self.scale_goal

                else:
                    # highlighted, go back
                    self.scale_goal = self.scale_goal_saved
                    self.scale_goal_saved = None

            self.card_pressed = True
            return True

            # debug print
            print("mouse clicked on sprite!")
            print("width  = ", self.width * self.scale)
            print("height = ", self.height * self.scale)
            print("x,y", x, y)
            self.card.print()
            print()
            print("------------------------")

        return False

    def reset_card_pressed(self):
        self.card_pressed = False

    def update(self, dt):

        if self.scale != self.scale_goal:
            if abs(self.scale - self.scale_goal) < self.scale_speed*dt:
                self.scale = self.scale_goal
            elif self.scale < self.scale_goal:
                self.scale += self.scale_speed*dt
            else:
                self.scale -= self.scale_speed * dt

        if self.target_pos is not None:
            current_pos = util.Point(self.x, self.y)
            move_dist = self.my_speed*dt

            """
            print("Card on the way! ", end="")
            print(current_pos, end="")
            print(" target pos is ", end="")
            print(self.target_pos)
            """

            if current_pos.distance_to(self.target_pos) > move_dist:
                # Move towards target
                target_dir = self.target_pos - current_pos
                target_dir.normalize()
                new_pos = current_pos + target_dir.multiply(move_dist)

                # Does not work for some reason
                #self.card_label.x = new_pos.x
                #self.card_label.y = new_pos.y

                self.x = new_pos.x
                self.y = new_pos.y

                self.alt_back.x = new_pos.x
                self.alt_back.y = new_pos.y

            else:
                # Just snap to position if in range
                self.x = self.target_pos.x
                self.y = self.target_pos.y

                # Does not work for some reason
                #self.card_label.x = self.target_pos.x
                #self.card_label.y = self.target_pos.y

                self.alt_back.x = self.target_pos.x
                self.alt_back.y = self.target_pos.y

                self.target_pos = None # Stops movement
                if self.final_target:
                    self.reached_final_target = True

        #print(self.x, " - ", self.card_label.x)

    def print(self):
        print("|" + self.operator + str(self.value) + " (" + str(self.cost) + ")|", end="")

    def return_print(self):
        return self.operator + str(self.value) + " (" + str(self.cost) + ")"

    def __repr__(self):
        return self.return_print()


class DeckVisual(pyglet.sprite.Sprite):
    def __init__(self, *args, count_below=True, count_enabled=True, **kwargs):

        self.window = kwargs["window"]
        del kwargs["window"]

        if "deck_position" in kwargs:
            self.deck_position = kwargs["deck_position"]
            del kwargs["deck_position"]

        initial_count = kwargs["initial_count"]
        del kwargs["initial_count"]

        super(DeckVisual, self).__init__(img=resources.card_back, *args, **kwargs)

        self.scale = 0.3

        if initial_count == 0:
            self.opacity = 120
        else:
            self.opacity = 230

        self.deck_count = pyglet.text.Label(text=str(initial_count), *args, **kwargs,
                                            anchor_x='center', anchor_y='center')

        if count_enabled:
            self.deck_count.opacity = 255
        else:
            self.deck_count.opacity = 0

        number_displacement = 80
        if count_below:
            self.deck_count.y -= number_displacement
            self.rotation = 180
        else:
            self.deck_count.y += number_displacement

    def update_count(self, n):
        self.deck_count.text = str(n)

        if n == 0:
            self.opacity = 128
        else:
            self.opacity = 230

    def update_deck_top(self, A_card):
        self.img = A_card.img
