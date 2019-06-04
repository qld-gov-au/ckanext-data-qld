Feature: Search with Google
  As an information seeker,
  I want to search specific keyword on Google
  so that I can obtain related info.

  Scenario: Run a simple search
    Given I am on the Google page
     When I search 'AlphaGo'
     Then I can see many results.

