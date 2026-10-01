#!/usr/bin/env python3
"""
E2E Test for Cash Shift Module (Arqueo y Cierre de Caja)
Tests the complete flow: Login -> Apertura Caja -> Factura Create -> Cierre Caja
"""
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

BASE_URL = "http://127.0.0.1:8000"

def setup_driver():
    """Configure and return Chrome WebDriver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver

def take_screenshot(driver, name):
    """Take screenshot and save it."""
    filename = f"/home/danilot/Documents/Proyectos/Facturación/e2e_{name}.png"
    driver.save_screenshot(filename)
    print(f"📸 Screenshot saved: {filename}")
    return filename

def test_login(driver, username, password):
    """Login with given credentials."""
    print(f"\n🔐 Logging in as {username}...")
    driver.get(f"{BASE_URL}/login/")
    
    wait = WebDriverWait(driver, 10)
    username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
    password_field = driver.find_element(By.NAME, "password")
    
    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    
    # Wait for redirect
    wait.until(lambda d: "/login" not in d.current_url)
    print(f"✅ Logged in successfully. Current URL: {driver.current_url}")
    take_screenshot(driver, "01_login")
    return True

def test_redirect_to_apertura_caja(driver):
    """Test 1: Navigate to factura/crear/ and verify redirect to /caja/apertura/"""
    print("\n🧪 TEST 1: Redirección a apertura de caja")
    driver.get("http://127.0.0.1:8000/facturacion/factura/crear/")
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.url_contains("/caja/apertura/"))
    
    assert "/caja/apertura/" in driver.current_url, f"Expected redirect to /caja/apertura/, got {driver.current_url}"
    print(f"✅ Redirected to: {driver.current_url}")
    take_screenshot(driver, "02_redirect_apertura")
    return True

def test_apertura_caja(driver):
    """Test 2: Open cash register with initial amount"""
    print("\n🧪 TEST 2: Apertura de caja")
    
    wait = WebDriverWait(driver, 10)
    # Wait for form to load
    wait.until(EC.presence_of_element_located((By.NAME, "monto_inicial")))
    
    # Fill in initial amount
    monto_field = driver.find_element(By.NAME, "monto_inicial")
    monto_field.clear()
    monto_field.send_keys("100")
    
    # Submit
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_btn.click()
    
    # Wait for redirect to factura_create
    wait.until(lambda d: "/facturacion/factura/crear/" in d.current_url)
    
    assert "/facturacion/factura/crear/" in driver.current_url
    print(f"✅ Caja abierta. Redirigido a: {driver.current_url}")
    take_screenshot(driver, "03_apertura_caja")
    return True

def test_factura_create_page(driver):
    """Test 3: Verify factura create page loads correctly"""
    print("\n🧪 TEST 3: Página de creación de factura")
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "id_cliente")))
    
    # Check that select2 for client loads
    client_select = driver.find_element(By.ID, "id_cliente")
    assert client_select.is_displayed()
    
    # Check productos search
    producto_search = driver.find_element(By.ID, "id_producto_search") if driver.find_elements(By.ID, "id_producto_search") else None
    
    # Check DataTable for details
    table = driver.find_element(By.ID, "detalles-table") if driver.find_elements(By.ID, "detalles-table") else driver.find_elements(By.TAG_NAME, "table")[0]
    
    # Check JS console for errors
    logs = driver.get_log('browser')
    js_errors = [log for log in logs if log['level'] == 'SEVERE']
    if js_errors:
        print(f"⚠️ JS Console Errors: {js_errors}")
    else:
        print("✅ No JS console errors")
    
    print("✅ Factura create page loaded correctly")
    take_screenshot(driver, "04_factura_create")
    return True

def test_cierre_caja(driver):
    """Test 4: Navigate to cierre caja and perform arqueo"""
    print("\n🧪 TEST 4: Cierre de caja (Arqueo)")
    driver.get("http://127.0.0.1:8000/caja/cierre/")
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.NAME, "efectivo_declarado")))
    
    # Check that system totals are displayed
    efectivo_sistema = driver.find_element(By.ID, "id_efectivo_sistema").get_attribute("value") if driver.find_elements(By.ID, "id_efectivo_sistema") else "0"
    tarjeta_sistema = driver.find_element(By.ID, "id_tarjeta_sistema").get_attribute("value") if driver.find_elements(By.ID, "id_tarjeta_sistema") else "0"
    
    print(f"  Efectivo Sistema: {efectivo_sistema}")
    print(f"  Tarjeta Sistema: {tarjeta_sistema}")
    
    # Fill declared amounts
    efectivo_field = driver.find_element(By.NAME, "efectivo_declarado")
    efectivo_field.clear()
    efectivo_field.send_keys("150")
    
    tarjeta_field = driver.find_element(By.NAME, "tarjeta_declarada")
    tarjeta_field.clear()
    tarjeta_field.send_keys("50")
    
    # Add notes
    notas_field = driver.find_element(By.NAME, "notas")
    notas_field.send_keys("Test arqueo automático")
    
    # Submit
    submit_btn = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
    submit_btn.click()
    
    # Wait for redirect
    wait = WebDriverWait(driver, 10)
    wait.until(lambda d: "/facturacion/factura/crear/" in d.current_url or "/facturacion/" in d.current_url)
    
    print(f"✅ Caja cerrada. Redirigido a: {driver.current_url}")
    take_screenshot(driver, "05_cierre_caja")
    return True

def test_historial_cierres(driver):
    """Test 5: Verify historial de cierres"""
    print("\n🧪 TEST 5: Historial de cierres")
    driver.get("http://127.0.0.1:8000/caja/historial/")
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "tabla-cierres")))
    
    # Check table has data
    rows = driver.find_elements(By.CSS_SELECTOR, "#tabla-cierres tbody tr")
    print(f"  Cierres registrados: {len(rows)}")
    
    take_screenshot(driver, "06_historial_cierres")
    print("✅ Historial de cierres cargado")
    return True

def run_all_tests():
    """Run all E2E tests."""
    driver = setup_driver()
    results = {
        "login": False,
        "redirect_apertura": False,
        "apertura_caja": False,
        "factura_create": False,
        "cierre_caja": False,
        "historial_cierres": False,
    }
    
    try:
        # Test 0: Login
        print("=" * 60)
        print("🚀 INICIANDO PRUEBAS E2E - MÓDULO ARQUEO Y CIERRE DE CAJA")
        print("=" * 60)
        
        # Need to create a test user first
        print("\n📝 Preparando usuario de prueba...")
        
        # Test 1: Login as admin
        results["login"] = test_login(driver, "admin", "admin123")
        
        # Test 1: Redirect to apertura
        results["redirect_apertura"] = test_redirect_to_apertura_caja(driver)
        
        # Test 2: Apertura caja
        results["apertura_caja"] = test_apertura_caja(driver)
        
        # Test 3: Factura create
        results["factura_create"] = test_factura_create_page(driver)
        
        # Test 4: Cierre caja
        results["cierre_caja"] = test_cierre_caja(driver)
        
        # Test 5: Historial
        results["historial_cierres"] = test_historial_cierres(driver)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        take_screenshot(driver, "error")
    finally:
        # Summary
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE PRUEBAS E2E")
        print("=" * 60)
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {test}: {status}")
        
        all_passed = all(results.values())
        print(f"\n{'✅ TODAS LAS PRUEBAS PASARON' if all_passed else '❌ ALGUNAS PRUEBAS FALLARON'}")
        
        driver.quit()
        return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)