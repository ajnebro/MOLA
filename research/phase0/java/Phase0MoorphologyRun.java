// Phase 0, check 6.2 (impact): run moorphology master (9d57172) on ZDT1 and print its JSON.
// The instrumented build adds phase0_* keys holding the global rank statistics read immediately
// after the global ranking, before the neighbourhood loop can overwrite them.
package xyz.jfaldanam.moorphology;

import org.uma.jmetal.problem.multiobjective.zdt.ZDT1;
import org.uma.jmetal.util.pseudorandom.JMetalRandom;

public class Phase0MoorphologyRun {
  public static void main(String[] args) {
    for (int d : new int[] {2, 4}) {
      JMetalRandom.getInstance().setSeed(42);
      ProblemCharacterization pc = new ProblemCharacterization();
      pc.calculateCharacteristics(new ZDT1(d), 200 * d);
      System.out.println(pc.toString());
    }
  }
}
