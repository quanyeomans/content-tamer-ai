Feature: Simple Document Processing
  As a user
  I want to see that document processing works
  So that I can trust the system

  @bdd @golden_path
  Scenario: User sees processing starts
    Given I have a test directory
    When I create a simple test file
    Then I should see the file exists