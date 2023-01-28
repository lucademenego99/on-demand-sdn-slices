from custom_events import EventTest, SliceUpdateEvent

class EventsHandler(object):
    """
    This class is used to send events to the GUI.
    """
    def __init__(self, send_ev_func, send_ev_to):
        """
        :param send_ev_func: Function to send events to the GUI
        :param send_ev_to: Destination of the events
        """
        super(EventsHandler, self).__init__()
        self.send_event = send_ev_func
        self.to = send_ev_to
    
    def send_test(self, arg):
        """
        Send a test event to the GUI
        :param arg: event argument
        """
        print("sending event")
        print(type(arg))
        self.send_event(self.to, EventTest(arg))
    
    def send_slice_update(self, arg):
        """
        Send a slice update event to the GUI
        :param arg: event argument
        """
        self.send_event(self.to, SliceUpdateEvent(arg))
