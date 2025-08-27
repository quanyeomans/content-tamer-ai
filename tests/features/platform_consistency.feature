Feature: Cross-Platform User Experience
  As a user on any operating system
  I want consistent behavior and clear file path handling
  So that the tool works reliably regardless of platform

  @bdd
  Scenario: Processing works consistently with different path separators
    Given I have a clean platform test environment
    When I create files with platform-appropriate paths
    Then file processing should handle paths correctly
    And the results should be consistent regardless of path format

  @bdd @golden_path
  Scenario: Error messages are platform-appropriate
    Given I have a clean platform test environment
    When I encounter file path errors
    Then error messages should be clear and platform-appropriate
    And file operations should handle platform differences gracefully

  @bdd
  Scenario: Display output works across different terminal environments
    Given I have a clean platform test environment
    When I run processing with various display options
    Then the display should work correctly
    And special characters should be handled appropriately