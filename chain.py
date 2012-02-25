class ChainAPI(object):
    """Decorator to set certain options on a function"""
    def __init__(self, bypass=False, allowed=True):
        self.bypass = bypass
        self.allowed = allowed
    
    def __call__(self, func):
        # Make sure the result of this function
        # Does not implicitly clobber current value on chain
        func.keep_current = True
        
        # Set function to return it's value instead of the chain
        if self.bypass:
            func.bypass_chain = True
        
        # Set function to raise an error when accessed via internals.use
        if not self.allowed:
            func.not_allowed_from_chain = True
        
        return func

class ChainInternals(object):
    """Internal management for state of the chain"""
    def __init__(self, proxy=None, strict_proxy=True, **options):
        self.proxy = proxy
        if not proxy:
            self.proxy = options.get('proxy', None)
        self.options = options
        self.options['strict_proxy'] = strict_proxy
        
        self._current = None
        self._last_current = None
        self.meaningful_current = False
        
        self.proxy_stack = []
        self.stored_values = {}
        self.named_proxies = {}
    
    @property
    def current(self):
        """Used by call_current to call the last accessed thing"""
        return self._current
    
    @property
    def current_value(self):
        """
            Used by API to access the current value
            Different to current only if a chain method is access via self.use
        """
        return self._last_current
    
    @current.setter
    def current(self, value):
        """
            To ensure API still has access to self.current after self.use is used,
            The current value is always stored on both self._current and self._last_current
            And self.use will manually set self._last_current to the current value,
            after setting self._current to the function to be called next when choosing an internals attribute
        """
        self._current = value
        self._last_current = value
    
    @current_value.setter
    def current_value(self, value):
        """set self._last_current to something different to self._current"""
        self._last_current = value
    
    @ChainAPI(allowed=False)
    def use(self, key):
        if key.startswith("chain_"):
            attr = getattr(self, key[6:])
            if hasattr(attr, 'not_allowed_from_chain') and attr.not_allowed_from_chain:
                raise AttributeError("Not allowed to use %s" % key)
            
            if self.meaningful_current:
                value = self.current
            else:
                value = self.current_value
            
            # Next time we do a chain API call, we don't want to preserver this current
            self.meaningful_current = False
            
            # self.current is needed for call_current
            # self.current_value is used by self.current when it's called
            self.current = attr
            self.current_value = value
        else:
            # Next time we do a chain API call, we want to preserve this current
            self.meaningful_current = True
            try:
                self.current = getattr(self.proxy, key)
            except AttributeError:
                self.current = None
                if self.options.get('strict_proxy', False):
                    raise AttributeError("Proxy (%s) does not have %s" % (self.proxy, key))
    
    @ChainAPI(allowed=False)
    def call_current(self, *args, **kwargs):
        current = self.current
        if self.options['strict_proxy'] or current and callable(current):
            result = current(*args, **kwargs)
            if not hasattr(current, 'keep_current') or not current.keep_current:
                self.current = result
            
            if hasattr(current, 'bypass_chain') and current.bypass_chain:
                # Return a tuple, incase result of calling current is None
                # This way we can distinguish between calls that bypass the chain
                # And ones that don't
                return (result, )
    
    @ChainAPI(bypass=True)
    def exit(self):
        """Bypass chain and return all stored values"""
        return self.proxy
    
    @ChainAPI(bypass=True)
    def get_stored(self):
        """Bypass chain and return all stored values"""
        return self.stored_values
    
    @ChainAPI(bypass=True)
    def retrieve(self, name):
        """Bypass chain and return current value"""
        return self.stored_values[name]
    
    @ChainAPI()
    def tap(self, action):
        """Call the provided action with the current value and don't change current value"""
        return action(self.current_value)

    @ChainAPI()
    def store(self, name):
        """Store current value under a particular name"""
        self.stored_values[name] = self.current_value
    
    @ChainAPI()
    def promote_value(self, value=None):
        """Use current value as proxy"""
        self.proxy_stack.append(self.proxy)
        if value is None:
            value = self.current_value
        self.proxy = value
    
    @ChainAPI()
    def demote_value(self):
        """Remove current proxy and use previous proxy instead"""
        self.proxy = None
        if self.proxy_stack:
            self.proxy = self.proxy_stack.pop()
    
    @ChainAPI()
    def call_proxy(self):
        """Set current value to proxy so calling the chain calls the proxy"""
        self.current = self.proxy
    
    @ChainAPI()
    def name_proxy(self, name):
        """Give the current proxy a name"""
        self.named_proxies[name] = self.proxy
    
    @ChainAPI()
    def restore_proxy(self, name):
        """Set the proxy to the proxy that was given the provided name"""
        self.promote_value(self.named_proxies[name])
    
    @ChainAPI()
    def replace_proxy(self, new_proxy):
        """Replace current proxy with new_proxy"""
        self.promote_value(new_proxy)
    
    @ChainAPI()
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