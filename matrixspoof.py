#!/usr/bin/env python3

#pylint:disable=E1101

from typing import (
    Sequence,
)

import functools

from migen import (
    Module,
    Signal,
    Replicate,
)

from migen.fhdl.verilog import convert


class YAggregator(Module):
    yin: Signal
    yout: Signal
    _width: int

    def __init__(self, width: int) -> None:
        if width < 1:
            raise ValueError('Width must be >= 1.')

        self._width = width
        self.yin = Signal(width)
        self.yout = Signal()

        self.comb += self.yout.eq(functools.reduce(Signal.__or__, self.yin))

    @property
    def width(self) -> int:
        return self._width


class XSelector(Module):
    sel: Signal
    cgin: Signal
    cgout: Signal
    _width: int

    def __init__(self, width: int) -> None:
        self._width = width
        self.sel = Signal()
        self.selext = Replicate(self.sel, width)
        self.cgin = Signal(width)
        self.cgout = Signal(width)
        self.comb += self.cgout.eq(self.selext & self.cgin)


class MatrixSpoof(Module):
    aggregators: Sequence[YAggregator]
    selectors: Sequence[XSelector]
    xin: Signal
    yout: Signal
    cgin: Signal

    def __init__(self, ndrivers: int, nsensors: int) -> None:
        self.aggregators = tuple(YAggregator(ndrivers) for _ in range(nsensors))
        self.selectors = tuple(XSelector(nsensors) for _ in range(ndrivers))

        self.xin = Signal(ndrivers)
        self.yout = Signal(nsensors)
        # cgin is accessed with X index
        self.cgin = tuple(Signal(nsensors) for _ in range(ndrivers))

        self.submodules.aggregators = self.aggregators
        self.submodules.selectors = self.selectors

        for sink, source in zip(self.yout, self.aggregators):
            self.comb += sink.eq(source.yout)

        for sink, source in zip(self.selectors, self.xin):
            self.comb += sink.sel.eq(source)

        for source, sink in zip(self.cgin, (selector.cgin for selector in self.selectors)):
            self.comb += sink.eq(source)

        for sindex, selector in enumerate(self.selectors):
            for aindex, aggregator in enumerate(self.aggregators):
                self.comb += aggregator.yin[sindex].eq(selector.cgout[aindex])
