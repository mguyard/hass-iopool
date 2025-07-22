"""
pytest-html configuration for iopool integration tests.
"""
import os
import pytest
from datetime import datetime


def pytest_html_report_title(report):
    """Set the HTML report title."""
    report.title = "iopool Home Assistant Integration - Test Report"


def pytest_configure(config):
    """Configure pytest-html metadata."""
    # Add project metadata using the _metadata attribute (modern pytest-html)
    if hasattr(config, '_metadata'):
        config._metadata["Project"] = "hass-iopool"
        config._metadata["Description"] = "Home Assistant Custom Integration for iopool pool monitoring"
        config._metadata["Repository"] = "https://github.com/mguyard/hass-iopool"
        config._metadata["Test Environment"] = "GitHub Actions"
        config._metadata["Report Generated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Add CI environment information if available
        if "HA_VERSION" in os.environ:
            config._metadata["Home Assistant Version"] = os.environ["HA_VERSION"]
        if "GITHUB_REF" in os.environ:
            config._metadata["Git Branch"] = os.environ["GITHUB_REF"].replace("refs/heads/", "")
        if "GITHUB_SHA" in os.environ:
            config._metadata["Git Commit"] = os.environ["GITHUB_SHA"][:8]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Enhanced test reporting with screenshot capability."""
    pytest_html = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    
    # Add extra information to failed tests
    if report.when == "call" and report.failed and pytest_html:
        # Add test details to the report
        test_details = []
        
        # Add test function docstring if available
        if hasattr(item.function, "__doc__") and item.function.__doc__:
            test_details.append(f"<div><strong>Test Description:</strong><br/>{item.function.__doc__.strip()}</div>")
        
        # Add test parameters if any
        if hasattr(item, "callspec") and item.callspec.params:
            params_str = ", ".join([f"{k}={v}" for k, v in item.callspec.params.items()])
            test_details.append(f"<div><strong>Test Parameters:</strong> {params_str}</div>")
        
        # Add fixture information
        if hasattr(item, "fixturenames"):
            fixtures = [f for f in item.fixturenames if not f.startswith("_")]
            if fixtures:
                test_details.append(f"<div><strong>Used Fixtures:</strong> {', '.join(fixtures)}</div>")
        
        # Add test file and line number
        test_details.append(f"<div><strong>Test Location:</strong> {item.fspath}::{item.name}</div>")
        
        # Add timestamp
        test_details.append(f"<div><strong>Failed At:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>")
        
        # Note: For actual screenshots, you would need selenium or similar
        # This is a placeholder for screenshot functionality
        if hasattr(item, "_screenshot_path"):
            screenshot_html = (
                "<div><strong>Screenshot:</strong><br/>"
                f"<img src='{item._screenshot_path}' alt='Test Screenshot' "
                "style='max-width: 100%; height: auto;'/></div>"
            )
            test_details.append(screenshot_html)
        
        # Combine all extra information
        if test_details:
            extra_html = (
                "<div style='margin-top: 10px; padding: 10px; border-left: 3px solid #f44336; "
                "background-color: #ffebee;'>"
            )
            extra_html += "<h4 style='margin-top: 0; color: #c62828;'>Additional Test Information</h4>"
            extra_html += "".join(test_details)
            extra_html += "</div>"
            
            # Add the extra HTML to the report
            if not hasattr(report, "extra"):
                report.extra = []
            report.extra.append(pytest_html.extras.html(extra_html))


def pytest_html_results_table_header(cells):
    """Customize the results table header."""
    cells.insert(2, "<th>Test Module</th>")


def pytest_html_results_table_row(report, cells):
    """Customize the results table rows."""
    # Add test module information
    test_module = getattr(report, "nodeid", "").split("::")[0].split("/")[-1]
    cells.insert(2, f"<td>{test_module}</td>")


def pytest_html_results_summary(prefix, summary, postfix):
    """Customize the results summary."""
    prefix.extend([
        "<p><strong>Integration:</strong> iopool Home Assistant Custom Component</p>",
        "<p><strong>Test Suite:</strong> Unit Tests with Home Assistant Test Framework</p>",
        "<p><strong>Coverage:</strong> See CodeCov for detailed coverage analysis</p>",
    ])
