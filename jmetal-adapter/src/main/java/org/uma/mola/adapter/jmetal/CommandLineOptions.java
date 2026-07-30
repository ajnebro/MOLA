package org.uma.mola.adapter.jmetal;

/** The optional {@code --variables}/{@code --sample-size}/{@code --seed} flags, parsed once. */
record CommandLineOptions(Integer variables, Integer sampleSize, Long seed) {

  /**
   * Parses flag/value pairs from {@code args}, starting at {@code startIndex}.
   *
   * @throws IllegalArgumentException if a flag is unknown, missing its value, or the value isn't
   *     a valid number
   */
  static CommandLineOptions parse(String[] args, int startIndex) {
    Integer variables = null;
    Integer sampleSize = null;
    Long seed = null;
    for (int index = startIndex; index < args.length; index += 2) {
      String flag = args[index];
      String value = valueAfter(args, index, flag);
      switch (flag) {
        case "--variables" -> variables = Integer.parseInt(value);
        case "--sample-size" -> sampleSize = Integer.parseInt(value);
        case "--seed" -> seed = Long.parseLong(value);
        default -> throw new IllegalArgumentException("unknown option: " + flag);
      }
    }
    return new CommandLineOptions(variables, sampleSize, seed);
  }

  private static String valueAfter(String[] args, int index, String flag) {
    if (index + 1 >= args.length) {
      throw new IllegalArgumentException("missing value for " + flag);
    }
    return args[index + 1];
  }
}
