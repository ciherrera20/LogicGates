from gates import Project, Nand, Reshaper, Datetime, Constant
from gates.utils import ProgramEncoder
import json

if __name__ == '__main__':
    # Open project from the save file
    # with open('../saves/test0.json', 'r') as f:
    #     obj = json.load(f)['project']
    # gates = {}
    # project = Project.deserialize(obj, gates)

    project = Project('test')

    TestA = project.define('TestA', [1], [1])
    TestA.tie_input_to_output(0, 0)

    TestB = project.define('TestB', [1], [1])
    testA0 = TestA()
    TestB.add_gate(testA0)
    TestB.add_connection((testA0, 0), (0, testA0))
    TestB.tie_output_to((testA0, 0), 0)

    TestC = project.define('TestC', [1], [1])
    testB0 = TestB()
    TestC.add_gate(testB0)
    TestC.tie_output_to((testB0, 0), 0)

    TestD = project.define('TestD', [1], [1])
    testC0 = TestC()
    TestD.add_gate(testC0)
    TestD.tie_output_to((testC0, 0), 0)

    # nand0 = Nand()  # gate 0
    # nand1 = Nand()  # gate 1

    # Stateful = project.define('Stateful', [1], [1])  # gates 2 and 3
    # Stateful.add_gate(nand0)
    # Stateful.add_connection((nand0, 0), (1, nand0))
    # Stateful.tie_input_to(0, (0, nand0))
    # Stateful.tie_output_to((nand0, 0), 0)

    # stateful0 = Stateful()  # gate 4
    # constant0 = Constant(1)  # gate 5
    # constant0.set_state([1])

    # Clock = project.define('Clock', [], [1])  # gates 6 and 7
    # Clock.add_gate(stateful0)
    # Clock.add_gate(constant0)
    # Clock.add_connection((constant0, 0), (0, stateful0))
    # Clock.tie_output_to((stateful0, 0), 0)

    # Test = project.define('Test')  # gates 8 and 9
    # clock0 = Clock()  # gate 10
    # Test.add_gate(clock0)

    # Stateful.remove_gate(nand0)
    # Stateful.add_gate(nand1)
    # Stateful.add_connection((nand1, 0), (1, nand1))
    # Stateful.tie_input_to(0, (0, nand1))
    # Stateful.tie_output_to((nand1, 0), 0)

    # # Not = project.define('NOT')
    # # Not.append_input(1)
    # # Not.append_output(1)
    # # nand0 = Nand()
    # # Not.add_gate(nand0)
    # # Not.tie_input_to(0, (0, nand0))
    # # Not.tie_input_to(0, (1, nand0))
    # # Not.tie_output_to((nand0, 0), 0)

    # # Clock = project.define('CLOCK', [], [1])
    # # not0 = Not()
    # # Clock.add_gate(not0)
    # # Clock.add_connection((not0, 0), (0, not0))
    # # Clock.tie_output_to((not0, 0), 0)

    # # And = project.define('AND', [1, 1], [1])
    # # nand0 = Nand()
    # # nand1 = Nand()
    # # And.add_gate(nand0)
    # # And.add_gate(nand1)
    # # And.tie_input_to(0, (0, nand0))
    # # And.tie_input_to(1, (1, nand0))
    # # And.add_connection((nand0, 0), (0, nand1))
    # # And.add_connection((nand0, 0), (1, nand1))
    # # And.tie_output_to((nand1, 0), 0)

    # # Or = project.define('OR', [1, 1], [1])
    # # not0 = Not()
    # # not1 = Not()
    # # nand0 = Nand()
    # # Or.add_gate(not0)
    # # Or.add_gate(not1)
    # # Or.add_gate(nand0)
    # # Or.tie_input_to(0, (0, not0))
    # # Or.tie_input_to(1, (0, not1))
    # # Or.add_connection((not0, 0), (0, nand0))
    # # Or.add_connection((not1, 0), (1, nand0))
    # # Or.tie_output_to((nand0, 0), 0)

    # # Nor = project.define('NOR', [1, 1], [1])
    # # or0 = Or()
    # # not0 = Not()
    # # Nor.add_gate(or0)
    # # Nor.add_gate(not0)
    # # Nor.tie_input_to(0, (0, or0))
    # # Nor.tie_input_to(1, (1, or0))
    # # Nor.add_connection((or0, 0), (0, not0))
    # # Nor.tie_output_to((not0, 0), 0)

    # # And8bit = project.define('AND8bit', [8, 8], [8])
    # # reshaper0 = Reshaper([8, 8], [1]*16)
    # # and0 = And()
    # # and1 = And()
    # # and2 = And()
    # # and3 = And()
    # # and4 = And()
    # # and5 = And()
    # # and6 = And()
    # # and7 = And()
    # # reshaper1 = Reshaper([1]*8, [8])

    # # And8bit.add_gate(reshaper0)
    # # And8bit.add_gate(and0)
    # # And8bit.add_gate(and1)
    # # And8bit.add_gate(and2)
    # # And8bit.add_gate(and3)
    # # And8bit.add_gate(and4)
    # # And8bit.add_gate(and5)
    # # And8bit.add_gate(and6)
    # # And8bit.add_gate(and7)
    # # And8bit.add_gate(reshaper1)

    # # And8bit.tie_input_to(0, (0, reshaper0))
    # # And8bit.tie_input_to(1, (1, reshaper0))

    # # And8bit.add_connection((reshaper0, 0), (0, and0))
    # # And8bit.add_connection((reshaper0, 1), (0, and1))
    # # And8bit.add_connection((reshaper0, 2), (0, and2))
    # # And8bit.add_connection((reshaper0, 3), (0, and3))
    # # And8bit.add_connection((reshaper0, 4), (0, and4))
    # # And8bit.add_connection((reshaper0, 5), (0, and5))
    # # And8bit.add_connection((reshaper0, 6), (0, and6))
    # # And8bit.add_connection((reshaper0, 7), (0, and7))

    # # And8bit.add_connection((reshaper0, 8), (1, and0))
    # # And8bit.add_connection((reshaper0, 9), (1, and1))
    # # And8bit.add_connection((reshaper0, 10), (1, and2))
    # # And8bit.add_connection((reshaper0, 11), (1, and3))
    # # And8bit.add_connection((reshaper0, 12), (1, and4))
    # # And8bit.add_connection((reshaper0, 13), (1, and5))
    # # And8bit.add_connection((reshaper0, 14), (1, and6))
    # # And8bit.add_connection((reshaper0, 15), (1, and7))

    # # And8bit.add_connection((and0, 0), (0, reshaper1))
    # # And8bit.add_connection((and1, 0), (1, reshaper1))
    # # And8bit.add_connection((and2, 0), (2, reshaper1))
    # # And8bit.add_connection((and3, 0), (3, reshaper1))
    # # And8bit.add_connection((and4, 0), (4, reshaper1))
    # # And8bit.add_connection((and5, 0), (5, reshaper1))
    # # And8bit.add_connection((and6, 0), (6, reshaper1))
    # # And8bit.add_connection((and7, 0), (7, reshaper1))

    # # And8bit.tie_output_to((reshaper1, 0), 0)

    # # OnOffClock = project.define('OnOffClock', [1], [1], input_labels=('tog',))
    # # clock0 = Clock()
    # # and0 = And()
    # # OnOffClock.add_gate(clock0)
    # # OnOffClock.add_gate(and0)
    # # OnOffClock.tie_input_to(0, (0, and0))
    # # OnOffClock.add_connection((clock0, 0), (1, and0))
    # # OnOffClock.tie_output_to((and0, 0), 0)

    # # RsNorLatch = project.define('RsNorLatch', [1, 1], [1, 1])
    # # nor0 = Nor()
    # # nor1 = Nor()
    # # not0 = Not()
    # # RsNorLatch.add_gate(nor0)
    # # RsNorLatch.add_gate(nor1)
    # # RsNorLatch.add_gate(not0)
    # # RsNorLatch.tie_input_to(0, (0, nor0))
    # # RsNorLatch.tie_input_to(1, (0, nor1))
    # # RsNorLatch.add_connection((nor0, 0), (1, nor1))
    # # RsNorLatch.add_connection((nor1, 0), (1, nor0))
    # # RsNorLatch.add_connection((nor1, 0), (0, not0))
    # # RsNorLatch.tie_output_to((nor1, 0), 1)
    # # RsNorLatch.tie_output_to((not0, 0), 0)