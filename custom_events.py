from ryu.controller import event

class EventTest(event.EventBase):
    """
    This event is used to test the websocket connection and the event system
    """
    def __init__(self, dp):
        super(EventTest, self).__init__()
        self.dp = dp

class SliceUpdateEvent(event.EventBase):
    """
    This event is used to test notify a slice update
    """
    def __init__(self, slice_template):
        super(SliceUpdateEvent, self).__init__()
        self.slice_template=slice_template