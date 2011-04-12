import policy

class EventState(object):

    """ Represents the current state of events """

    overrides = {}
    """ A mapping of resource names to the overridden policy name for that
    resource, if there is one. """

    def __init__(self):
        self.overrides = {}

    def override(self, resource, policy):
        self.overrides[resource.name] = policy

    def overridden_policy(self, resource):
        """ Return the policy class for this resource, or None if there is not
        an overridden policy. """
        if resource.name in self.overrides:
            policy_name = self.overrides[resource.name]
            return resource.policies[policy_name]
        else:
            return None

    def policy(self, resource):
        selected = self.overridden_policy(resource)
        if not selected:
            if resource.policy is not None:
                selected = resource.policy.literal_policy(resource)
            else:
                selected = resource.policies.default()
        return selected(resource)

# module level global to preserve event state
# may get rolled in to context eventually if we can do it without
# making life hell
state = EventState()

def reset():
    global state
    state = EventState()
