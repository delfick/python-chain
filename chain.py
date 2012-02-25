class Decorate(object):
    """Decorator to set certain options on a function"""
    def __init__(self, bypass=False, allowed=True):
        self.bypass = bypass
        self.allowed = allowed
        self.proxy_stack = []
        self.stored_values = {}
        self.named_proxies = {}
    
    def __call__(self, func):
        if self.bypass:
            func.bypass_chain = True
        
        if not self.allowed:
            func.not_allowed_from_chain = True
        
        return func

class ChainInternals(object):
    """Internal management for state of the chain"""
    def __init__(self, strict_proxy=True, **options):
        self.proxy = options.get('proxy', None)
        self.options = options
        self.options['strict_proxy'] = strict_proxy
        
        self.current = None
        self.stored_values = {}
    
    @Decorate(allowed=False)
    def use(self, key):
        if key.startswith("chain_"):
            attr = getattr(self, key[6:])
            if hasattr(attr, 'not_allowed_from_chain') and attr.not_allowed_from_chain:
                raise AttributeError("Not allowed to use %s" % key)
            
            self.current = attr
        else:
            if hasattr(self.proxy, key):
                self.current = getattr(self.proxy, key)
            else:
                if self.options.get('strict_proxy', False):
                    raise AttributeError("Proxy does not have %s" % key)
                else:
                    self.current = None
    
    @Decorate(allowed=False)
    def call_current(self, *args, **kwargs):
        current = self.current
        if self.options['strict_proxy'] or current and callable(current):
            self.current = current(*args, **kwargs)
            if hasattr(current, 'bypass_chain') and current.bypass_chain:
                # Return a tuple, incase result of calling current is None
                # This way we can distinguish between calls that bypass the chain
                # And ones that don't
                return (self.current, )
    
    @Decorate(bypass=True)
    def exit(self):
        """Bypass chain and return all stored values"""
        return self.proxy
    
    @Decorate(bypass=True)
    def get_stored(self):
        """Bypass chain and return all stored values"""
        return self.stored_values
    
    @Decorate(bypass=True)
    def retrieve(self, name):
        """Bypass chain and return current value"""
        return self.stored_values[name]
    
    def tap(self, action):
        """Call the provided action with the current value and don't change current value"""
        return action(self.current)

    def store(self, name):
        """Store current value under a particular name"""
        self.stored_values[name] = self.current
    
    def promote_value(self, value=None):
        """Use current value as proxy"""
        self.proxy_stack.append(self.proxy)
        if value is None:
            value = self.current
        self.proxy = value
    
    def demote_value(self):
        """Remove current proxy and use previous proxy instead"""
        self.proxy = None
        if self.proxy_stack:
            self.proxy = self.proxy_stack.pop()
    
    def call_proxy(self):
        """Set current value to proxy so calling the chain calls the proxy"""
        self.current = self.proxy
    
    def replace_proxy(self, new_proxy):
        """Replace current proxy with new_proxy"""
        self.proxy = new_proxy
    
    def name_proxy(self, name):
        """Give the current proxy a name"""
        self.named_proxies[name] = self.proxy
    
    def restore_proxy(self, name):
        """Set the proxy to the proxy that was given the provided name"""
        self.promote_value(self.named_proxies[name])
    
    def setattr(self, key, value):
        """Call setattr on the proxy with provided key and value"""
        setattr(self.proxy, key, value)

class Chain(object):
    """Exposed API for creating a chain to proxy some object"""
    def __init__(self, proxy=None, **options):
        self.internals = ChainInternals(proxy, **options)
    
    def __getattribute__(self, key):
        object.__getattribute__(self, 'internals').use(key)
        return self
    
    def __call__(self, *args, **kwargs):
        val = object.__getattribute__(self, 'internals').call_current(*args, **kwargs)
        # If val is nothing, then return the chain
        # Otherwise it is a tuple of (result, ). Return result
        if val:
            return val[0]
        else:
            return self
    
    def __dir__(self):
        internals = object.__getattribute__(self, 'internals')
        proxy = internals.proxy
        result = ['chain_%s' % k for k in dir(internals)]
        if proxy:
            return result + dir(proxy)
        else:
            return result