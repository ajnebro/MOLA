package xyz.jfaldanam.moorphology;

import org.apache.commons.math3.stat.correlation.SpearmansCorrelation;
import org.json.JSONObject;
import org.uma.jmetal.component.catalogue.common.solutionscreation.impl.LatinHypercubeSamplingSolutionsCreation;
import org.uma.jmetal.problem.doubleproblem.impl.AbstractDoubleProblem;
import org.uma.jmetal.problem.ProblemFactory;
import org.uma.jmetal.solution.doublesolution.DoubleSolution;
import org.uma.jmetal.util.ranking.Ranking;
import org.uma.jmetal.util.ranking.impl.FastNonDominatedSortRanking;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.DoubleStream;

/**
 * Characterization of continuous MOOPs (Multi-objective optimisation Problems).
 * Global Characteristics to study of each problem (ref: <a href="https://dl.acm.org/doi/pdf/10.1145/3449639.3459353">https://dl.acm.org/doi/pdf/10.1145/3449639.3459353</a>):
 * - Distances among solutions in the VARIABLE space (avg, max)
 * - Distances among solutions in the OBJECTIVE space (avg, max)
 * - avg and max Rank w.r.t. non dominated sorting
 * - entropy of the number of solutions per rank w.r.t. non-dominated sorting
 **/
public class ProblemCharacterization {
    private static final SpearmansCorrelation spearmansCalculator = new SpearmansCorrelation();
    private final JSONObject characteristicsJson;

    /**
     * Create an empty instance of the problem characterization class
     **/
    public ProblemCharacterization() {
        this.characteristicsJson = new JSONObject();
    }

    /**
     * Store the characteristics calculated to a file in json format
     **/
    public void toFile(String filename) {
        try (PrintWriter outputWriter = new PrintWriter(new FileWriter(filename))) {
            outputWriter.write(characteristicsJson.toString(2));
        } catch (IOException e) {
            System.err.println("Error writing to output file: " + filename);
            System.exit(1);
        }
    }

    /**
     * Dump the characteristics calculated as a string in json format.
     **/
    @Override
    public String toString() {
        return characteristicsJson.toString(2);
    }

    /**
     * Example main method to calculate the characteristics of a set of problems from jMetal.
     **/
    public static void main(String[] args) throws FileNotFoundException {
        if (args.length < 1) {
            System.err.println("Missing parameter for output filename.");
            System.exit(-1);
        }
        String filename = args[0];

        // Define problems to calculate characteristics from
        List<AbstractDoubleProblem> problemList = new ArrayList<>();

        for (int i = 1; i < args.length; i++) {
            String problemName = args[i];
            AbstractDoubleProblem problem = (AbstractDoubleProblem) ProblemFactory.<DoubleSolution>loadProblem(problemName);
            problemList.add(problem);
        }

        // Calculate the characteristics
        ProblemCharacterization problemCharacterization = new ProblemCharacterization();
        problemCharacterization.calculateCharacteristics(problemList);
        problemCharacterization.toFile(filename);
    }

    /**
     * Calculate characteristics using 200*d samples, where is d the number of variables, as defined by the reference article.
     **/
    public void calculateCharacteristics(List<AbstractDoubleProblem> problems) {
        for (AbstractDoubleProblem problem : problems) {
            calculateCharacteristics(problem, 200 * problem.numberOfVariables());
        }
    }

    /**
     * Adds a double to a json object, changing it to "NaN" if it is non-finite.
     * Required as org.json doesn't support infinite values as doubles.
     **/
    private void putDouble(JSONObject json, String key, double value) {
        if (Double.isFinite(value))
            json.put(key, value);
        else
            json.put(key, "NaN");
    }

    /**
     * Calculate all implemented characteristics for a continuous problem
     **/
    public void calculateCharacteristics(AbstractDoubleProblem problem, int numSamples) {
        int neighborhoodSize = problem.numberOfVariables();

        JSONObject problemCharacteristics = new JSONObject();
        problemCharacteristics.put("name", problem.name());
        problemCharacteristics.put("sampleSize", numSamples);
        problemCharacteristics.put("numberOfObjectives", problem.numberOfObjectives());
        problemCharacteristics.put("numberOfVariables", problem.numberOfVariables());
        problemCharacteristics.put("numberOfConstraints", problem.numberOfConstraints());

        // Calculate max euclidean distance
        double DIST_X_MAX_GLOBAL = Math.sqrt(problem.variableBounds().stream() // For each Variable
                .map(b -> Math.pow(b.getUpperBound() - b.getLowerBound(), 2)) // Calculate the square of the difference of the bounds
                .mapToDouble(Double::doubleValue).sum());
        putDouble(problemCharacteristics, "distanceXMaximumAnalytically", DIST_X_MAX_GLOBAL);

        // Create and evaluate NUM_SAMPLES solutions
        LatinHypercubeSamplingSolutionsCreation sampleCreator = new LatinHypercubeSamplingSolutionsCreation(problem, numSamples);
        List<DoubleSolution> sampleSolutions = sampleCreator.create();
        sampleSolutions.forEach(problem::evaluate);

        // Create a ranking of the samples
        Ranking<DoubleSolution> ranking = new FastNonDominatedSortRanking<>();
        ranking.compute(sampleSolutions);
        List<DoubleSolution> non_dominated_solutions = ranking.getSubFront(0);

        double[][] variableDistanceCache = new double[sampleSolutions.size()][sampleSolutions.size()];
        double[][] objectiveDistanceCache = new double[sampleSolutions.size()][sampleSolutions.size()];
        double dist_var_sum = 0;
        double DIST_X_MAX = Double.NEGATIVE_INFINITY;
        double DIST_X_MIN = Double.POSITIVE_INFINITY;
        double dist_obj_sum = 0;
        double DIST_F_MAX = Double.NEGATIVE_INFINITY;
        double DIST_F_MIN = Double.POSITIVE_INFINITY;
        double dist_var_nd_sum = 0;
        double DIST_X_ND_MAX = Double.NEGATIVE_INFINITY;
        // This matrix is symmetrical, we don't need to iterate through n^2
        for (int i = 0; i < sampleSolutions.size(); i++) {
            for (int j = i; j < sampleSolutions.size(); j++) {
                double var_distance = getVariableDistance(sampleSolutions.get(i), sampleSolutions.get(j));
                double obj_distance = getObjectiveDistance(sampleSolutions.get(i), sampleSolutions.get(j));

                variableDistanceCache[i][j] = var_distance;
                variableDistanceCache[j][i] = var_distance;
                objectiveDistanceCache[i][j] = obj_distance;
                objectiveDistanceCache[j][i] = obj_distance;

                dist_var_sum += var_distance;
                DIST_X_MAX = Math.max(var_distance, DIST_X_MAX);
                DIST_X_MIN = Math.min(var_distance, DIST_X_MIN);

                dist_obj_sum += obj_distance;
                DIST_F_MAX = Math.max(obj_distance, DIST_F_MAX);
                DIST_F_MIN = Math.min(var_distance, DIST_F_MIN);

                // If both solutions are non dominated
                if (non_dominated_solutions.contains(sampleSolutions.get(i)) && non_dominated_solutions.contains(sampleSolutions.get(i))) {
                    dist_var_nd_sum += var_distance;
                    DIST_X_ND_MAX = Math.max(var_distance, DIST_X_ND_MAX);
                }
            }
        }

        // For the averages, we are iterating through n(n+1)/2 cells of the n^2 matrix in the loop above
        double DIST_X_AVG = dist_var_sum / ((sampleSolutions.size() * (sampleSolutions.size() + 1)) / 2.0);
        double DIST_F_AVG = dist_obj_sum / ((sampleSolutions.size() * (sampleSolutions.size() + 1)) / 2.0);
        double DIST_X_ND_AVG = dist_var_nd_sum / non_dominated_solutions.size();

        // Normalization of non-max data
        if (Math.abs(DIST_X_MAX) < 1 || Math.abs(DIST_F_MAX) < 1)
            System.err.println("WARNING: Normalization with max value < 1");
        double DIST_X_AVG_NORM = (DIST_X_AVG - DIST_X_MIN) / (DIST_X_MAX - DIST_X_MIN);
        double DIST_F_AVG_NORM = (DIST_F_AVG - DIST_F_MIN) / (DIST_F_MAX - DIST_F_MIN);
        double DIST_X_ND_AVG_NORM = (DIST_X_ND_AVG - DIST_X_MIN) / (DIST_X_MAX - DIST_X_MIN);

        putDouble(problemCharacteristics, "distanceXMaximum", DIST_X_MAX);
        putDouble(problemCharacteristics, "distanceXAverage", DIST_X_AVG_NORM);
        putDouble(problemCharacteristics, "distanceFMaximum", DIST_F_MAX);
        putDouble(problemCharacteristics, "distanceFAverage", DIST_F_AVG_NORM);
        putDouble(problemCharacteristics, "distanceXNonDominatedMaximum", DIST_X_ND_MAX);
        putDouble(problemCharacteristics, "distanceXNonDominatedAverage", DIST_X_ND_AVG_NORM);

        // Get neighborhood for each sample.
        Map<Integer, Set<Integer>> neighborhood = getNeighbours(variableDistanceCache, neighborhoodSize);

        double neigh_dist_var_sum = 0;
        double NEIGH_DIST_X_MAX = Double.NEGATIVE_INFINITY;
        double neigh_dist_obj_sum = 0;
        double NEIGH_DIST_F_MAX = Double.NEGATIVE_INFINITY;
        double sup_neig_sum = 0;
        double inf_neig_sum = 0;
        double inc_neig_sum = 0;
        double lnd_neig_sum = 0;
        double lsup_neig_sum = 0;

        Map<Integer, double[]> neighbours_variable_distance = new HashMap<Integer, double[]>();
        Map<Integer, double[]> neighbours_objective_distance = new HashMap<Integer, double[]>();
        for (Map.Entry<Integer, Set<Integer>> entry : neighborhood.entrySet()) {

            int referenceSample = entry.getKey();
            Set<Integer> currentNeighborhood = entry.getValue();

            double[] variableDistances = getDistancesFromNeighbours(referenceSample, currentNeighborhood, variableDistanceCache);
            double[] objectiveDistances = getDistancesFromNeighbours(referenceSample, currentNeighborhood, objectiveDistanceCache);
            neighbours_variable_distance.put(referenceSample, variableDistances);
            neighbours_objective_distance.put(referenceSample, objectiveDistances);

            double meanVariableDistance = Arrays.stream(variableDistances).sum() / variableDistances.length;
            double meanObjectiveDistance = Arrays.stream(objectiveDistances).sum() / objectiveDistances.length;

            neigh_dist_var_sum = meanVariableDistance;
            NEIGH_DIST_X_MAX = Math.max(meanVariableDistance, NEIGH_DIST_X_MAX);
            neigh_dist_obj_sum = meanObjectiveDistance;
            NEIGH_DIST_F_MAX = Math.max(meanObjectiveDistance, NEIGH_DIST_F_MAX);

            // Global ranking
            int referenceGlobalRank = ranking.getRank(sampleSolutions.get(referenceSample));
            double local_sup_neig_sum = 0;
            double local_inf_neig_sum = 0;
            double local_inc_neig_sum = 0;
            double local_lnd_neig_sum = 0;
            double local_lsup_neig_sum = 0;
            for (Integer neighbour : currentNeighborhood) {
                int neigGlobalRank = ranking.getRank(sampleSolutions.get(neighbour));
                if (referenceGlobalRank == neigGlobalRank)
                    local_inc_neig_sum++; // neighbour is incomparable
                else if (referenceGlobalRank < neigGlobalRank)
                    local_inf_neig_sum++; // neighbour is dominated
                else if (referenceGlobalRank > neigGlobalRank)
                    local_sup_neig_sum++; // neighbour is dominating
            }

            // Local ranking
            List<DoubleSolution> doubleSolutionsNeighborhood = currentNeighborhood.stream().map(sampleSolutions::get).collect(Collectors.toList());
            doubleSolutionsNeighborhood.add(sampleSolutions.get(referenceSample));

            Ranking<DoubleSolution> neig_ranking = new FastNonDominatedSortRanking<>();
            neig_ranking.compute(doubleSolutionsNeighborhood);

            int referenceRank = neig_ranking.getRank(sampleSolutions.get(referenceSample));
            for (Integer neighbour : currentNeighborhood) {
                int neigRank = ranking.getRank(sampleSolutions.get(neighbour));
                if (referenceRank == neigRank)
                    local_lnd_neig_sum++; // neighbour is incomparable
                else if (referenceRank < neigRank)
                    local_lsup_neig_sum++; // neighbour is dominated
            }

            sup_neig_sum += local_sup_neig_sum / neighborhoodSize;
            inf_neig_sum += local_inf_neig_sum / neighborhoodSize;
            inc_neig_sum += local_inc_neig_sum / neighborhoodSize;
            lnd_neig_sum += local_lnd_neig_sum / neighborhoodSize;
            lsup_neig_sum += local_lsup_neig_sum / neighborhoodSize;
        }

        double NEIGH_DIST_X_AVG = neigh_dist_var_sum / sampleSolutions.size();
        double NEIGH_DIST_F_AVG = neigh_dist_obj_sum / sampleSolutions.size();

        double SUP_AVG_NEIG = sup_neig_sum / sampleSolutions.size();
        double INF_AVG_NEIG = inf_neig_sum / sampleSolutions.size();
        double INC_AVG_NEIG = inc_neig_sum / sampleSolutions.size();
        double LND_AVG_NEIG = lnd_neig_sum / sampleSolutions.size();
        double LSUP_AVG_NEIG = lsup_neig_sum / sampleSolutions.size();

        // Normalization of non-max data
        double NEIGH_DIST_X_AVG_NORM = (NEIGH_DIST_X_AVG - DIST_X_MIN) / (DIST_X_MAX - DIST_X_MIN);
        double NEIGH_DIST_F_AVG_NORM = (NEIGH_DIST_F_AVG - DIST_F_MIN) / (DIST_F_MAX - DIST_F_MIN);

        putDouble(problemCharacteristics, "neighbourDistanceXMaximum", NEIGH_DIST_X_MAX);
        putDouble(problemCharacteristics, "neighbourDistanceXAverage", NEIGH_DIST_X_AVG_NORM);
        putDouble(problemCharacteristics, "neighbourDistanceFMaximum", NEIGH_DIST_F_MAX);
        putDouble(problemCharacteristics, "neighbourDistanceFAverage", NEIGH_DIST_F_AVG_NORM);
        putDouble(problemCharacteristics, "averageProportionOfDominatingNeighbours", SUP_AVG_NEIG);
        putDouble(problemCharacteristics, "averageProportionOfDominatedNeighbours", INF_AVG_NEIG);
        putDouble(problemCharacteristics, "averageProportionOfIncomparableNeighbours", INC_AVG_NEIG);
        putDouble(problemCharacteristics, "averageProportionOfLocallyNonDominatedNeighbours", LND_AVG_NEIG);
        putDouble(problemCharacteristics, "averageProportionOfSupportedLocallyNonDominatedNeighbours", LSUP_AVG_NEIG);


        // Calculate correlations
        double dist_x_cor_neig_sum = 0;
        int dist_x_cor_neig_count = 0;
        double dist_f_cor_neig_sum = 0;
        int dist_f_cor_neig_count = 0;
        for (Map.Entry<Integer, Set<Integer>> entry : neighborhood.entrySet()) {
            int referenceSample = entry.getKey();
            for (Integer neighbour : entry.getValue()) {
                double[] x_dist_ref = neighbours_variable_distance.get(referenceSample);
                double[] x_dist_neig = neighbours_variable_distance.get(neighbour);
                double[] f_dist_ref = neighbours_objective_distance.get(referenceSample);
                double[] f_dist_neig = neighbours_objective_distance.get(neighbour);

                // Ensure there is at least 2 neighbours to allow to calculate the spearman's correlation,
                // else skip it for the mean.
                if (x_dist_ref.length >= 2 || x_dist_neig.length >= 2) {
                    dist_x_cor_neig_sum += spearmansCalculator.correlation(
                            x_dist_ref,
                            x_dist_neig
                    );
                    dist_x_cor_neig_count+=1;
                }
                if (f_dist_ref.length >= 2 || f_dist_neig.length >= 2) {
                    dist_f_cor_neig_sum += spearmansCalculator.correlation(
                            f_dist_ref,
                            f_dist_neig
                    );
                    dist_f_cor_neig_count += 1;
                }
            }
        }

        double DIST_X_COR_NEIGH = dist_x_cor_neig_sum / dist_x_cor_neig_count;
        double DIST_F_COR_NEIGH = dist_f_cor_neig_sum / dist_f_cor_neig_count;
        putDouble(problemCharacteristics, "neighboursCorrelationOfAverageDistanceX", DIST_X_COR_NEIGH);
        putDouble(problemCharacteristics, "neighboursCorrelationOfAverageDistanceF", DIST_F_COR_NEIGH);

        //System.out.println("NUM_RANKS: " + ranking.getNumberOfSubFronts());
        List<Integer> ranks = sampleSolutions.stream().map(s -> ranking.getRank(s)).collect(Collectors.toList());
        double NON_DOMINATED_PROPORTION = ranking.getSubFront(0).size() / (double) numSamples;
        int RANK_MAX = ranks.stream().mapToInt(Integer::intValue).max().getAsInt();
        double RANK_AVG = ranks.stream().mapToInt(Integer::intValue).average().getAsDouble();
        double RANK_ENTROPY = getRankEntropy(ranks, RANK_MAX);
        putDouble(problemCharacteristics, "proportionOfNonDominated", NON_DOMINATED_PROPORTION);
        problemCharacteristics.put("rankMaximum", RANK_MAX);
        problemCharacteristics.put("rankAverage", RANK_AVG);
        putDouble(problemCharacteristics, "rankEntropy", RANK_ENTROPY);

        characteristicsJson.put(problem.name(), problemCharacteristics);
    }

    /**
     * For each solution of a sample, get its d closest neighbours
     **/
    public static Map<Integer, Set<Integer>> getNeighbours(List<DoubleSolution> samples, int d) {
        // For each solution x ∈ P, we additionally define its d closest solutions from
        // the sample other than x as its neighbours, d being the problem dimension.

        double[][] distances = new double[samples.size()][samples.size()];
        for (int i = 0; i < samples.size(); i++) {
            for (int j = i; j < samples.size(); j++) {
                double var_distance = getVariableDistance(samples.get(i), samples.get(j));

                distances[i][j] = var_distance;
                distances[j][i] = var_distance;
            }
        }

        return getNeighbours(distances, d);
    }

    // parameter samples can be remove
    /**
     * Calculate the d closes neighbours to each solution according to a distance matrix
     **/
    public static Map<Integer, Set<Integer>> getNeighbours(double[][] distances, int d) {
        Map<Integer, Set<Integer>> neighboursMap = new HashMap<Integer, Set<Integer>>();

        for (int reference = 0; reference < distances.length; reference++) {
            Set<Integer> neighbours = new HashSet<Integer>();
            List<Double> distanceRow = DoubleStream.of(distances[reference]).boxed().collect(Collectors.toList());
            // Get the d neighbours
            for (int k = 0; k < d; k++) {
                double minDistance = Collections.min(distanceRow);
                int index = distanceRow.indexOf(minDistance);
                if (index != reference)
                    neighbours.add(index);
                distanceRow.set(index, Double.POSITIVE_INFINITY);
            }
            neighboursMap.put(reference, neighbours);
        }

        return neighboursMap;
    }

    /**
     * Calculate the <a href="https://en.wikipedia.org/wiki/Entropy_(information_theory)">entropy</a> of the distributions of ranks
     **/
    public static double getRankEntropy(List<Integer> ranks, int maxRank) {
        // https://en.wikipedia.org/wiki/Entropy_(information_theory)
        int[] rankFreq = new int[maxRank + 1];
        double entropy = 0;
        int n = ranks.size();

        // Calculate the frequencies for each rank
        for (int rank : ranks) {
            rankFreq[rank]++;
        }

        // Calculate the entropy
        for (int freq : rankFreq) {
            if (freq > 0) {
                double p = 1.0 * freq / n;
                entropy -= p * Math.log(p) / Math.log(2);
            }
        }
        return entropy;
    }

    /**
     * Calculate the distance between one solution and its neighbours according to a distance matrix
     **/
    public static double[] getDistancesFromNeighbours(int referenceSolution, Set<Integer> neighbours, double[][] distanceMatrix) {
        /*
         * Returns variable distances and objective distances
         */
        double[] distances = new double[neighbours.size()];
        Integer[] tmp_neighbours = neighbours.toArray(new Integer[0]);
        for (int i = 0; i < neighbours.size(); i++) {
            distances[i] = distanceMatrix[referenceSolution][tmp_neighbours[i]];
        }
        return distances;
    }

    /**
     * Calculate the distance between two solutions in the variable space
     **/
    public static double getVariableDistance(DoubleSolution sol1, DoubleSolution sol2) {
        // Both solutions must have the same number of variables
        // https://en.wikipedia.org/wiki/Euclidean_distance#Higher_dimensions
        double distance_sum = 0;

        for (int i = 0; i < sol1.variables().size(); i++)
            distance_sum += Math.pow(sol1.variables().get(i) - sol2.variables().get(i), 2);

        double result = Math.sqrt(distance_sum);
        if (!Double.isFinite(result))
            throw new InputMismatchException("Distance between:\n" + sol1 + "and:\n " + sol2 + "is not finite");

        return result;
    }

    /**
     * Calculate the distance between two solutions in the objective space
     **/
    public static double getObjectiveDistance(DoubleSolution sol1, DoubleSolution sol2) {
        // Both solutions must have the same number of objectives
        // https://en.wikipedia.org/wiki/Euclidean_distance#Higher_dimensions
        double distance_sum = 0;

        for (int i = 0; i < sol1.objectives().length; i++)
            distance_sum += Math.pow(sol1.objectives()[i] - sol2.objectives()[i], 2);

        double result = Math.sqrt(distance_sum);
        if (!Double.isFinite(result))
            throw new InputMismatchException("Distance between:\n" + sol1 + "and:\n" + sol2 + "is not finite");

        return result;
    }
}
