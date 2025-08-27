Feature: Error Handling and User Communication
  As a user
  I want to understand what went wrong when files can't be processed
  So that I can take appropriate action

  @error_condition @critical @bdd
  Scenario: User sees clear feedback for file processing failures
    Given I have a clean test environment
    When I simulate a file processing failure
    Then I should see clear error communication
    And the error count should be incremented
    And I should understand what went wrong

  @error_condition @bdd
  Scenario: User sees recovery information when files succeed after retries
    Given I have a clean test environment
    When I simulate a file that succeeds after retry attempts
    Then I should see recovery success information
    And the final result should show success not failure
    And I should see appropriate retry statistics

  @golden_path @bdd
  Scenario: User sees accurate progress statistics during mixed outcomes
    Given I have a clean test environment
    When I simulate processing 3 successful files and 2 failed files
    Then I should see 3 files marked as successful
    And I should see 2 files marked as failed
    And the total count should equal 5 files processed
    And the statistics should be mathematically consistent