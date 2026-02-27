import os
import pytest
from playwright.sync_api import Page, expect
import time
import requests

def test_playground_load(page: Page):
    """Test if the Playground UI loads correctly."""
    page.goto("http://localhost:5173")
    expect(page.locator("text=SCPI Playground & Validation")).to_be_visible(timeout=10000)
    expect(page.locator("text=Single SCPI Execution")).to_be_visible()

def test_instrument_connection(page: Page):
    """Test connecting to simulated instruments and fetching status."""
    page.goto("http://localhost:5173")
    
    # Click Connect (Sim)
    connect_btn = page.locator("button:has-text('Connect (Sim)')")
    connect_btn.click()
    
    # Wait for connection to establish and list to populate
    expect(page.locator("text=Connected").first).to_be_visible(timeout=15000)
    
    # Verify at least one instrument (e.g., CMW500) is shown
    expect(page.locator("text=CMW500").first).to_be_visible()

def test_single_scpi_execution(page: Page):
    """Test sending a single SCPI command."""
    page.goto("http://localhost:5173")
    
    # Connect first
    page.locator("button:has-text('Connect (Sim)')").click()
    expect(page.locator("text=Connected").first).to_be_visible(timeout=15000)
    
    # Select the first instrument
    page.locator(".MuiPaper-root .MuiBox-root").filter(has_text="Connected").first.click()
    
    # Find the SCPI command input and run button
    cmd_input = page.get_by_label("SCPI Command")
    cmd_input.fill("*IDN?")
    
    page.locator("button:has-text('Send')").click()
    
    # In simulation mode, the response for *IDN? should contain "Simulated Instrument"
    expect(page.locator("text=Simulated Instrument")).to_be_visible(timeout=5000)

def test_batch_scpi_execution(page: Page):
    """Test the batch SCPI interoperability runner."""
    page.goto("http://localhost:5173")
    
    # Connect and select instrument
    page.locator("button:has-text('Connect (Sim)')").click()
    expect(page.locator("text=Connected").first).to_be_visible(timeout=15000)
    page.locator(".MuiPaper-root .MuiBox-root").filter(has_text="Connected").first.click()
    
    # Fill the batch textarea
    batch_input = page.locator("textarea").first
    batch_input.fill("*IDN?\\n*OPT?\\nSYST:ERR?")
    
    # Run batch
    page.locator("button:has-text('Run Batch Test')").click()
    
    # We should see the results table appear with the commands
    expect(page.locator("table")).to_be_visible(timeout=10000)
    
    # Verify the commands are in the table
    expect(page.locator("td:has-text('*IDN?')")).to_be_visible()
    expect(page.locator("td:has-text('*OPT?')")).to_be_visible()
