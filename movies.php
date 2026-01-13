<?php
error_reporting(0);
ini_set('display_errors', 0);
header("Content-Type: application/json");

$file = __DIR__ . '/movies.json';

// Initialize file if not exists
if (!file_exists($file)) {
    file_put_contents($file, json_encode([]));
    chmod($file, 0666);
}

function sendResponse($data) {
    echo json_encode($data);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];

function scrapeMovie($name) {
    $searchUrl = "https://www.google.com/search?q=" . urlencode($name . " terabox link");
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $searchUrl);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
    
    $html = curl_exec($ch);
    curl_close($ch);

    if (!$html) return null;

    if (preg_match('/https?:\/\/(?:www\.)?(?:1024)?terabox\.(?:com|app|tech)\/s\/[a-zA-Z0-9_-]+/', $html, $matches)) {
        return $matches[0];
    }

    return null;
}

if ($method === 'GET') {
    $search = isset($_GET['search']) ? strtolower(trim($_GET['search'])) : '';
    
    if (empty($search)) {
        sendResponse(['status' => 'error', 'message' => 'No search term provided']);
    }

    $movies = json_decode(file_get_contents($file), true);
    if (!is_array($movies)) $movies = [];
    
    foreach ($movies as $movie) {
        if (strtolower(trim($movie['name'])) === $search) {
            sendResponse(['status' => 'found', 'link' => $movie['link'] ?? '']);
        }
    }

    // AUTO SCRAP FALLBACK
    $scrapedLink = scrapeMovie($search);
    if ($scrapedLink) {
        $movies[] = ['name' => $search, 'link' => $scrapedLink];
        file_put_contents($file, json_encode($movies));
        sendResponse(['status' => 'found', 'link' => $scrapedLink]);
    }

    sendResponse(['status' => 'not_found']);

} elseif ($method === 'POST') {
    $action = $_POST['action'] ?? '';
    
    if ($action === 'add') {
        $name = $_POST['movie'] ?? '';
        $link = $_POST['link'] ?? '';
        
        if ($name && $link) {
            $movies = json_decode(file_get_contents($file), true);
            if (!is_array($movies)) $movies = [];
            
            // Check if exists
            foreach ($movies as $m) {
                if (strtolower(trim($m['name'])) === strtolower(trim($name))) {
                    sendResponse(['message' => 'Movie already exists']);
                }
            }
            
            $movies[] = ['name' => trim($name), 'link' => trim($link)];
            if (file_put_contents($file, json_encode($movies)) !== false) {
                sendResponse(['message' => 'Movie added successfully']);
            } else {
                sendResponse(['message' => 'Failed to write to file']);
            }
        } else {
            sendResponse(['message' => 'Movie name and link are required']);
        }
    } else {
        sendResponse(['message' => 'Invalid action']);
    }
}
?>
