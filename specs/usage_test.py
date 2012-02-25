# coding: spec

from chain import Chain
from shapes import Shapes

import fudge

describe "Chain Usage":
    describe "Simple case":
        @fudge.test
        it "just proxy's the object":
            ret1 = fudge.Fake('ret1')
            ret2 = fudge.Fake('ret2')
            
            kw1 = fudge.Fake('kw1')
            kw2 = fudge.Fake('kw2')
           
            arg1 = fudge.Fake('arg1')
            arg2 = fudge.Fake('arg2')
            
            proxy = (fudge.Fake().remember_order()
                .expects("call1").with_args(arg1)
                .expects("call2").returns(ret1)
                .expects("call3").with_args(kw1=kw1)
                .expects("call4").with_args(arg2)
                .expects("call5").returns(ret2)
                .expects("call6").with_args(arg1, arg2, kw1=kw1, kw2=kw2)
                )
            
            (Chain(proxy)
                .call1(arg1)
                .call2()
                .call3(kw1=kw1)
                .call4(arg2)
                .call5()
                .call6(arg1, arg2, kw1=kw1, kw2=kw2)
                )
    
    describe "Managing the proxy":
        it "is possible to add new proxies and go back to old ones":
            shapes = (
                Chain(Shapes())
                
                    .create('square')
                    .chain_promote_value()
                        .set_length(4)
                    .chain_demote_value()
                    
                    .create('rectangle')
                    .chain_promote_value()
                        .set_width(6)
                        .set_length(8)
                    .chain_demote_value()
                    
                .chain_exit()
                )
            
            shapes.shapes |should| have(2).shapes
        