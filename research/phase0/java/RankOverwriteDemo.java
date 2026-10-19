// Phase 0, check 6.2: does a second FastNonDominatedSortRanking computed on the SAME solution objects
// overwrite the ranks a first ranking reports? jMetal 6.1 stores the rank in solution.attributes()
// under getClass().getName(), so both rankings share the key.
import java.util.ArrayList;
import java.util.List;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.solution.doublesolution.impl.DefaultDoubleSolution;
import org.uma.jmetal.util.bounds.Bounds;
import org.uma.jmetal.util.ranking.Ranking;
import org.uma.jmetal.util.ranking.impl.FastNonDominatedSortRanking;

public class RankOverwriteDemo {
  static DoubleSolution solution(double f1, double f2) {
    List<Bounds<Double>> bounds = List.of(Bounds.create(0.0, 1.0));
    DoubleSolution s = new DefaultDoubleSolution(bounds, 2, 0);
    s.objectives()[0] = f1;
    s.objectives()[1] = f2;
    return s;
  }

  static String ranks(Ranking<DoubleSolution> r, List<DoubleSolution> all) {
    StringBuilder sb = new StringBuilder("[");
    for (DoubleSolution s : all) sb.append(r.getRank(s)).append(' ');
    return sb.toString().trim() + "]";
  }

  public static void main(String[] args) {
    // Four nested fronts: (i, i) for i = 0..3 -> global ranks 0,1,2,3
    List<DoubleSolution> all = new ArrayList<>();
    for (int i = 0; i < 4; i++) all.add(solution(i, i));
    Ranking<DoubleSolution> global = new FastNonDominatedSortRanking<>();
    global.compute(all);
    System.out.println("global ranks before local ranking : " + ranks(global, all));
    // Local ranking on a subset of the SAME objects (as moorphology does per neighbourhood)
    Ranking<DoubleSolution> local = new FastNonDominatedSortRanking<>();
    local.compute(new ArrayList<>(all.subList(2, 4)));
    System.out.println("global ranks after  local ranking : " + ranks(global, all));
    // Isolation: local ranking on COPIES leaves the global ranks intact
    Ranking<DoubleSolution> global2 = new FastNonDominatedSortRanking<>();
    global2.compute(all);
    List<DoubleSolution> copies = new ArrayList<>();
    for (DoubleSolution s : all.subList(2, 4)) copies.add((DoubleSolution) s.copy());
    new FastNonDominatedSortRanking<DoubleSolution>().compute(copies);
    System.out.println("global ranks after local ranking on copies: " + ranks(global2, all));
  }
}
