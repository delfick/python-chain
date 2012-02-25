# coding: spec

from chain import Decorate, ChainInternals, Chain

from fudge import patched_context
import fudge

describe "Decorate":
    it "sets bypass_chain on the function if bypass is True":
        def test(): pass
        test |should_not| respond_to("bypass_chain")
        
        Decorate(bypass=True)(test) |should| be(test)
        test.bypass_chain |should| be(True)
    
    it "sets not_allowed_from_chain to True if allowed is False":
        def test(): pass
        test |should_not| respond_to("not_allowed_from_chain")
        
        Decorate(allowed=False)(test) |should| be(test)
        test.not_allowed_from_chain |should| be(True)
    
    it "can set both bypass_chain and not_allowed_from_chain if specified":
        def test(): pass
        test |should_not| respond_to("bypass_chain")
        test |should_not| respond_to("not_allowed_from_chain")
        
        Decorate(bypass=True, allowed=False)(test) |should| be(test)
        test.bypass_chain |should| be(True)
        test.not_allowed_from_chain |should| be(True)
    
    it "does not set attributes it doesn't ask for":
        def test(): pass
        test |should_not| respond_to("bypass_chain")
        test |should_not| respond_to("not_allowed_from_chain")
        
        Decorate()(test) |should| be(test)
        test |should_not| respond_to("bypass_chain")
        test |should_not| respond_to("not_allowed_from_chain")

describe "ChainInternals":
    before_each:
        self.internals = ChainInternals()
        
    it "does not allowed use or call_current to be called from the chain":
        self.internals.use.not_allowed_from_chain |should| be(True)
        self.internals.call_current.not_allowed_from_chain |should| be(True)
    
    describe "Use":
        @fudge.test
        it "looks on internals if key starts with chain_":
            attr = fudge.Fake('attr')
            internals = type('test_ChainInternals', (ChainInternals, ), dict(existing_attr=attr))()
            internals.current |should| be(None)
            internals.use("chain_existing_attr")
            internals.current |should| be(attr)
            
        it "complains if key doesn't exist on internals":
            hasattr(self.internals, 'doesnt_exist') |should| be(False)
            AttributeError |should| be_thrown_by(lambda: self.internals.use('chain_doesnt_exist'))
        
        it "complains if attr on internals has not_allowed_from_chain set to True":
            @Decorate(allowed=False)
            def not_allowed_test():pass
            
            def allowed_test(): pass
            
            internals = type('test_ChainInternals'
                , (ChainInternals, )
                , dict(not_allowed_test=not_allowed_test, allowed_test=allowed_test)
                )()
            
            AttributeError |should| be_thrown_by(lambda: internals.use('chain_not_allowed_test'))
            AttributeError |should_not| be_thrown_by(lambda: internals.use('chain_allowed_test'))
        
        @fudge.test
        it "looks on proxy if key doesn't start with chain_":
            one = fudge.Fake('one')
            test = type('test', (object, ), dict(one=one))()
            self.internals.replace_proxy(test)
            self.internals.current |should| be(None)
            self.internals.use("one")
            self.internals.current |should| be(one)
            
        @fudge.test
        it "complains if value doesn't exist on proxy if options.strict_proxy is false":
            one = fudge.Fake('one')
            test = type('test', (object, ), dict(one=one))()
            self.internals.replace_proxy(test)
            self.internals.current |should| be(None)
            self.internals.options['strict_proxy'] = False
            self.internals.use("two")
            self.internals.current |should| be(None)
        
        @fudge.test
        it "sets current to None if can't find key on proxy if options.strict_proxy is true":
            one = fudge.Fake('one')
            test = type('test', (object, ), dict(one=one))()
            self.internals.replace_proxy(test)
            self.internals.current |should| be(None)
            self.internals.options['strict_proxy'] = True
            AttributeError |should| be_thrown_by(lambda: self.internals.use('two'))
    
    describe "Call Current":
        it "does nothing if there is not current or current isn't callable and strict_proxy is false":
            self.internals.current = None
            self.internals.options['strict_proxy'] = False
            Exception |should_not| be_thrown_by(lambda: self.internals.call_current())
            
        it "complains if there is not current or current isn't callable and strict_proxy is true":
            self.internals.current = None
            self.internals.options['strict_proxy'] = True
            Exception |should| be_thrown_by(lambda: self.internals.call_current())
        
        @fudge.test
        it "calls current with args and kwargs passed in":
            kw1 = fudge.Fake("kw1")
            kw2 = fudge.Fake("kw2")
            pos1 = fudge.Fake("pos1")
            pos2 = fudge.Fake("pos2")
            
            self.internals.current = (fudge.Fake("current").expects_call()
                .with_args(pos1, pos2, kw1=kw1, kw2=kw2)
                )
            
            self.internals.call_current(pos1, pos2, kw1=kw1, kw2=kw2)
        
        @fudge.test
        it "sets self.current to the return of the call":
            ret = fudge.Fake('ret')
            self.internals.current = fudge.Fake("current").expects_call().returns(ret)
            
            self.internals.call_current()
            self.internals.current |should| be(ret)
        
        @fudge.test
        it "returns the result as a single tuple if bypass_chain is true on self.current":
            ret = fudge.Fake('ret')
            self.internals.current = Decorate(bypass=True)(fudge.Fake("current").expects_call().returns(ret))
            
            self.internals.call_current() |should| equal_to((ret, ))
            self.internals.current |should| be(ret)
        
        @fudge.test
        it "returns nothing if bypass_chain is false on self.current":
            ret = fudge.Fake('ret')
            self.internals.current = Decorate(bypass=False)(fudge.Fake("current").expects_call().returns(ret))
            
            self.internals.call_current() |should| be(None)
            self.internals.current |should| be(ret)              

describe "Chain":
    @fudge.patch("chain.ChainInternals.__init__")
    it "creates an internals attribute that is a ChainInternals", fakeChainInternalsInit:
        kw1 = fudge.Fake("kw1")
        kw2 = fudge.Fake("kw2")
        proxy = fudge.Fake("proxy")
        internals = fudge.Fake("internals")
        fakeChainInternalsInit.expects_call().with_args(proxy, kw1=kw1, kw2=kw2)
        chain = Chain(proxy, kw1=kw1, kw2=kw2)
        object.__getattribute__(chain, 'internals') |should| be_instance_of(ChainInternals)
        
    @fudge.test
    it "calls use on internals with key when accessing an attribute":
        chain = Chain()
        internals = (fudge.Fake("internals").expects("use")
            .with_args("key1")
            .next_call().with_args("key2")
            .next_call().with_args("you_get_the_point")
            )

        internals.proxy = None
        
        chain.internals = internals
        chain.key1 |should| be(chain)
        chain.key2 |should| be(chain)
        chain.you_get_the_point |should| be(chain)
        
    describe "dir functionality":
        @fudge.test
        it "returns list of chain_ prefixed results from dir on internals and everything from dir(proxy)":
            proxy = fudge.Fake("proxy")
            internals = fudge.Fake("internals")
            internals.proxy = proxy
            
            chain = Chain()
            chain.internals = internals
            
            original_dir = dir
            def do_dir(obj):
                if obj is proxy:
                    return ['p1', 'p2', 'p3']
                elif obj is internals:
                    return ['i1', 'i2', 'i3']
                else:
                    return original_dir(obj)
            
            with patched_context("__builtin__", "dir", fudge.Fake("dir").expects_call().calls(do_dir)):
                dir(chain) |should| equal_to(['chain_i1', 'chain_i2', 'chain_i3', 'p1', 'p2', 'p3'])
    
    describe "Calling the chain":
        @fudge.test
        it "uses call_current on internals with args and kwargs provided":
            kw1 = fudge.Fake("kw1")
            kw2 = fudge.Fake("kw2")
            pos1 = fudge.Fake("pos1")
            pos2 = fudge.Fake("pos2")
            
            chain = Chain()
            chain.internals = (fudge.Fake("internals").expects("call_current")
                .with_args(pos1, pos2, kw1=kw1, kw2=kw2)
                )
            
            chain(pos1, pos2, kw1=kw1, kw2=kw2)
            
        @fudge.test
        it "returns val[0] returned val if not None":
            ret = fudge.Fake("ret")
            chain = Chain()
            chain.internals = fudge.Fake("internals").expects("call_current").returns((ret, ))
            chain() |should| be(ret)
            
        it "returns chain if returned val is None":
            ret = fudge.Fake("ret")
            chain = Chain()
            internals = fudge.Fake("internals").expects("call_current")
            internals.proxy = None
            chain.internals = internals
            chain() |should| be(chain)