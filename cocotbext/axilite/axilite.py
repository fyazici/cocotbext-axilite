
""" Driver for AXI4-Lite protocol """

import cocotb
from cocotb.triggers import RisingEdge, ReadWrite
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor


#pylint: disable=no-member
class AXI4LiteMaster(BusDriver):
    """AXI4-Lite Master
    """

    _signals = [
        "awvalid", "awready", "awaddr", 
        "wvalid", "wready", "wdata",
        "bvalid", "bready", "bresp",
        "arvalid", "arready", "araddr",
        "rvalid", "rready", "rdata", "rresp"
    ]

    def __init__(self, entity, name, clock, **kwargs):
        BusDriver.__init__(self, entity, name, clock, **kwargs)

        # defaults
        self.bus.awvalid.setimmediatevalue(0)
        self.bus.wvalid.setimmediatevalue(0)
        self.bus.bready.setimmediatevalue(0)
        self.bus.arvalid.setimmediatevalue(0)
        self.bus.rready.setimmediatevalue(0)

    async def write(self, waddr, wdata, timeout=None):
        self.bus.awvalid.value = 1
        self.bus.awaddr.value = waddr
        self.bus.wvalid.value = 1
        self.bus.wdata.value = wdata
        await RisingEdge(self.clock)

        while True:
            if self.bus.awready.value:
                self.bus.awvalid.value = 0
            if self.bus.wready.value:
                self.bus.wvalid.value = 0
            if (self.bus.awvalid == 0 and self.bus.wvalid == 0) or timeout == 0:
                break
            if timeout is not None:
                timeout -= 1
            await RisingEdge(self.clock)
        
        self.bus.bready.value = 1
        await RisingEdge(self.clock)

        while True:
            if self.bus.bvalid.value or timeout == 0:
                self.bus.bready.value = 0
                break
            if timeout is not None:
                timeout -= 1
            await RisingEdge(self.clock)

        if timeout == 0:
            return None

        return self.bus.bresp.value
    
    async def read(self, raddr, timeout=None):
        self.bus.arvalid.value = 1
        self.bus.araddr.value = raddr
        await RisingEdge(self.clock)

        while True:
            if self.bus.arready.value or timeout == 0:
                self.bus.arvalid.value = 0
                break
            if timeout is not None:
                timeout -= 1
            await RisingEdge(self.clock)
        
        self.bus.rready.value = 1
        await RisingEdge(self.clock)

        while True:
            if self.bus.rvalid.value or timeout == 0:
                self.bus.rready.value = 0
                break
            if timeout is not None:
                timeout -= 1
            await RisingEdge(self.clock)
        
        if timeout == 0:
            return (None, None)

        return (self.bus.rdata.value, self.bus.rresp.value)


class AXI4LiteSlaveMem(BusDriver):
    """AXI4-Lite Slave Mem
    """

    _signals = [
        "awvalid", "awready", "awaddr", 
        "wvalid", "wready", "wdata",
        "bvalid", "bready", "bresp",
        "arvalid", "arready", "araddr",
        "rvalid", "rready", "rdata", "rresp"
    ]

    def __init__(self, entity, name, clock, **kwargs):
        BusDriver.__init__(self, entity, name, clock, **kwargs)

        # defaults
        self.bus.awready.setimmediatevalue(0)
        self.bus.wready.setimmediatevalue(0)
        self.bus.bvalid.setimmediatevalue(0)
        self.bus.arready.setimmediatevalue(0)
        self.bus.rvalid.setimmediatevalue(0)

        self.mem = {}

    async def start(self):
        while True:
            # "wait for valid" type slave
            while True:
                if self.bus.awvalid.value and self.bus.wvalid.value:
                    self.bus.awready.value = 1
                    self.bus.wready.value = 1
                    break
                if self.bus.arvalid.value:
                    self.bus.arready.value = 1
                    break
                await RisingEdge(self.clock)
            await RisingEdge(self.clock)

            self.bus.awready.value = 0
            self.bus.wready.value = 0
            self.bus.arready.value = 0
            if self.bus.awvalid.value:
                self.mem[str(self.bus.awaddr.value)] = self.bus.wdata.value
                self.bus.bvalid.value = 1
                self.bus.bresp.value = 0
            else:
                self.bus.rvalid.value = 1
                if str(self.bus.araddr.value) in self.mem:
                    self.bus.rdata.value = self.mem[str(self.bus.araddr.value)]
                    self.bus.rresp.value = 0
                else:
                    self.bus.rresp.value = 1
            await RisingEdge(self.clock)

            while True:
                if self.bus.bvalid.value and self.bus.bready.value:
                    self.bus.bvalid.value = 0
                    break
                if self.bus.rvalid.value and self.bus.rready.value:
                    self.bus.rvalid.value = 0
                    break
                await RisingEdge(self.clock)
