from enum import Enum, auto
from typing import Dict, Type, Optional


class Event(Enum):
    """ Base enum for finite automation input."""
    pass


class State(Enum):
    """ Base enum for finite automation states."""
    Start = auto()  # initial automation state
    Finish = auto()  # final automation state

    def __rmatmul__(self, other: "Type[Automation]"):
        """ Binds automation class to current state."""
        return Automation(self)


class Condition:
    """ Condition for state transition."""
    def __init__(self, automation: "Automation"):
        self.automation = automation

    def __call__(self, event: Event) -> bool:
        """ returns True if event satisfies condition in current state."""
        raise NotImplementedError()

    def __or__(self, other: Type["Transition"]) -> "Transition":
        """ Binds condition to transition."""
        transition = other(self.automation)
        if self in self.automation.transitions:
            raise ValueError("Condition already added")
        self.automation.transitions[self] = transition
        return transition

    def __str__(self):
        return f'{self.automation.__class__.__name__}.{self.__class__.__name__}'


class OK(Condition):
    """ Condition that is always satisfied."""

    def __call__(self, event: Event) -> bool:
        return True


class Transition:
    """ Task called when moving from one state to another."""

    def __init__(self, automation: "Automation"):
        self.automation = automation
        self.next: Optional["Automation"] = None

    def __call__(self):
        raise NotImplementedError()

    def __gt__(self, other: State) -> "Automation":
        """ Binds transition to next state."""
        if self.next is not None:
            raise ValueError("Transition already bound")
        self.next = self.automation.clone(other)
        return self.next

    def __str__(self):
        return f'{self.automation.__class__.__name__}.{self.__class__.__name__}'


class Noop(Transition):
    """ Transition without any action."""

    def __call__(self):
        pass


class Automation:
    """ Automation in state."""

    def __init__(self, state: State):
        self.state = state
        """ Initial automation state."""
        self.transitions: Dict[Condition, Transition] = {}
        """ Automation transition table."""

    def __matmul__(self, other: Type[Condition]) -> Condition:
        """ Initializes new condition branch from current state."""
        return other(self)

    @property
    def finished(self) -> bool:
        return self.state == State.Finish

    def clone(self, state: State) -> "Automation":
        """
        Returns copy of current automation in another state with empty
        transition map.
        """
        return self.__class__.__call__(state)

    def next(self, event: Event) -> "Automation":
        transition = self._get_transition(event)
        self._run_transition(transition)
        return transition.next

    @staticmethod
    def _run_transition(transition: Transition):
        transition()

    def _get_transition(self, event: Event) -> Transition:
        satisfied_conditions = dict()
        transition = None
        for condition, transition in self.transitions.items():
            if condition(event):
                satisfied_conditions[condition] = transition
        if len(satisfied_conditions) == 0:
            raise RuntimeError("No satisfied conditions")
        if len(satisfied_conditions) > 1:
            raise RuntimeError("Multiple satisfied conditions")
        return transition


start = Automation @ State.Start

finish = start @ OK | Noop > State.Finish


a = start


class ExampleEvent(Event):
    X = auto()


while a.state != State.Finish:
    a = a.next(ExampleEvent.X)
