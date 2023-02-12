from Gate import Gate
from Nand import Nand
from Source import Source
from Sink import Sink
from Reshaper import Reshaper
from Project import Project
import json
from Serialize import ProgramEncoder

if __name__ == '__main__':
    project = Project('test')

    Not = project.define(1, 1, name='NOT')
    nand0 = Nand()
    Not.add_gate(nand0)
    Not.tie_input_to(0, (0, nand0))
    Not.tie_input_to(0, (1, nand0))
    Not.tie_output_to((nand0, 0), 0)

    Clock = project.define(0, 1, name='CLOCK')
    not0 = Not()
    Clock.add_gate(not0)
    Clock.add_connection((not0, 0), (0, not0))
    Clock.tie_output_to((not0, 0), 0)

    And = project.define(2, 1, name='AND') 
    nand1 = Nand()
    nand2 = Nand()
    And.add_gate(nand1)
    And.add_gate(nand2)
    And.tie_input_to(0, (0, nand1))
    And.tie_input_to(1, (1, nand1))
    And.add_connection((nand1, 0), (0, nand2))
    And.add_connection((nand1, 0), (1, nand2))
    And.tie_output_to((nand2, 0), 0)

    And_8bit = project.define(2, 1, name='AND_8bit')
    reshaper0 = Reshaper([8, 8], [1]*16)
    and0 = And()
    and1 = And()
    and2 = And()
    and3 = And()
    and4 = And()
    and5 = And()
    and6 = And()
    and7 = And()
    reshaper1 = Reshaper([1]*8, [8])

    And_8bit.add_gate(reshaper0)
    And_8bit.add_gate(and0)
    And_8bit.add_gate(and1)
    And_8bit.add_gate(and2)
    And_8bit.add_gate(and3)
    And_8bit.add_gate(and4)
    And_8bit.add_gate(and5)
    And_8bit.add_gate(and6)
    And_8bit.add_gate(and7)
    And_8bit.add_gate(reshaper1)

    And_8bit.tie_input_to(0, (0, reshaper0))
    And_8bit.tie_input_to(1, (1, reshaper0))

    And_8bit.add_connection((reshaper0, 0), (0, and0))
    And_8bit.add_connection((reshaper0, 1), (0, and1))
    And_8bit.add_connection((reshaper0, 2), (0, and2))
    And_8bit.add_connection((reshaper0, 3), (0, and3))
    And_8bit.add_connection((reshaper0, 4), (0, and4))
    And_8bit.add_connection((reshaper0, 5), (0, and5))
    And_8bit.add_connection((reshaper0, 6), (0, and6))
    And_8bit.add_connection((reshaper0, 7), (0, and7))

    And_8bit.add_connection((reshaper0, 8), (1, and0))
    And_8bit.add_connection((reshaper0, 9), (1, and1))
    And_8bit.add_connection((reshaper0, 10), (1, and2))
    And_8bit.add_connection((reshaper0, 11), (1, and3))
    And_8bit.add_connection((reshaper0, 12), (1, and4))
    And_8bit.add_connection((reshaper0, 13), (1, and5))
    And_8bit.add_connection((reshaper0, 14), (1, and6))
    And_8bit.add_connection((reshaper0, 15), (1, and7))

    And_8bit.add_connection((and0, 0), (0, reshaper1))
    And_8bit.add_connection((and1, 0), (1, reshaper1))
    And_8bit.add_connection((and2, 0), (2, reshaper1))
    And_8bit.add_connection((and3, 0), (3, reshaper1))
    And_8bit.add_connection((and4, 0), (4, reshaper1))
    And_8bit.add_connection((and5, 0), (5, reshaper1))
    And_8bit.add_connection((and6, 0), (6, reshaper1))
    And_8bit.add_connection((and7, 0), (7, reshaper1))

    And_8bit.tie_output_to((reshaper1, 0), 0)

    OnOffClock = project.define(1, 1, 'OnOffClock')
    clock0 = Clock()
    and8 = And()
    OnOffClock.add_gate(clock0)
    OnOffClock.add_gate(and8)
    OnOffClock.tie_input_to(0, (0, and8))
    OnOffClock.add_connection((clock0, 0), (1, and8))
    OnOffClock.tie_output_to((and8, 0), 0)