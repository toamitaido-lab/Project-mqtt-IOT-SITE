<?php
$db_path = __DIR__ . '/../db/iot_data.db';
try {
    $db = new PDO("sqlite:$db_path");
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Échec de connexion BDD : " . $e->getMessage());
}

// Récupération de l'historique brut
$rows = $db->query("SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 60")->fetchAll(PDO::FETCH_ASSOC);

// Fonction rapide pour extraire la dernière valeur d'une donnée calculée
function getLatestMetric($db, $metric_name) {
    $stmt = $db->prepare("SELECT calculated_value FROM derived_data WHERE metric_name = ? ORDER BY timestamp DESC LIMIT 1");
    $stmt->execute([$metric_name]);
    $row = $stmt->fetch(PDO::FETCH_ASSOC);
    return $row ? $row['calculated_value'] : "N/A";
}

$avg_mdm = getLatestMetric($db, 'avg_temp_mdm');
$avg_dax = getLatestMetric($db, 'avg_temp_dax');
$mean_between = getLatestMetric($db, 'mean_temp_mdm_dax');
?>
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5"> <title>[SUPERVISION] SAE203 Solution Stable</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0c0f12; color: #00f5d4; font-family: "Courier New", monospace; margin: 25px; }
        .metrics-grid { display: flex; gap: 15px; margin-bottom: 25px; }
        .card { background-color: #171c24; border: 2px solid #00f5d4; padding: 15px; flex: 1; text-align: center; font-size: 14px; font-weight: bold; }
        .card.mdm { border-color: #00f5d4; color: #00f5d4; }
        .card.dax { border-color: #ff9900; color: #ff9900; }
        .card.mix { border-color: #ff0055; color: #fff; background-color: #1a0f16; }
        .grid { display: flex; gap: 20px; flex-wrap: wrap; }
        .box { background: #171c24; border: 2px solid #00f5d4; padding: 20px; flex: 1; min-width: 450px; }
        table { width: 100%; border-collapse: collapse; font-size: 11px; }
        th { background-color: #ff0055; color: #fff; padding: 6px; }
        td { padding: 6px; border-bottom: 1px solid #0c0f12; color: #c5c6c7; }
    </style>
</head>
<body>

    <h1>[SYS_MONITORING] INFRASTRUCTURE IoT & CALCULS DERIVES</h1>
    
    <div class="metrics-grid">
        <div class="card mdm">🏠 MOYENNE GENERALE MDM : <?= $avg_mdm ?> °C</div>
        <div class="card dax">🌲 MOYENNE GENERALE DAX : <?= $avg_dax ?> °C</div>
        <div class="card mix">📊 MOYENNE INTER-VILLES : <?= $mean_between ?> °C</div>
    </div>

    <div class="grid">
        <div class="box">
            <h3>// SUPERPOSITION DES ENREGISTREMENTS THERMIQUES</h3>
            <div style="position: relative; height:300px;">
                <canvas id="iotChart"></canvas>
            </div>
        </div>

        <div class="box">
            <h3>// LOGS DU SERVEUR D'ACQUISITION</h3>
            <div style="max-height: 300px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr><th>TIMESTAMP</th><th>TOPIC VIRTUELE</th><th>VALEUR</th><th>UNITÉ</th></tr>
                    </thead>
                    <tbody>
                        <?php foreach ($rows as $row): ?>
                        <tr>
                            <td><?= htmlspecialchars($row['timestamp']) ?></td>
                            <td><?= htmlspecialchars($row['topic']) ?></td>
                            <td><?= htmlspecialchars($row['value']) ?></td>
                            <td><?= htmlspecialchars($row['unit']) ?></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const rawData = <?= json_encode($rows) ?>;
        const timeline = {};
        
        rawData.forEach(item => {
            if (!item.topic.includes('temp')) return;
            const timeLabel = item.timestamp.split(' ')[1]; // Format HH:MM:SS
            
            if (!timeline[timeLabel]) {
                timeline[timeLabel] = { mdm: null, dax: null };
            }
            if (item.topic.includes('mdm')) timeline[timeLabel].mdm = parseFloat(item.value);
            if (item.topic.includes('dax')) timeline[timeLabel].dax = parseFloat(item.value);
        });

        const sortedTimestamps = Object.keys(timeline).sort();
        const mdmData = sortedTimestamps.map(t => timeline[t].mdm);
        const daxData = sortedTimestamps.map(t => timeline[t].dax);

        new Chart(document.getElementById('iotChart').getContext('2d'), {
            type: 'line',
            data: {
                labels: sortedTimestamps,
                datasets: [
                    { label: 'Mont-de-Marsan', data: mdmData, borderColor: '#00f5d4', tension: 0.2, fill: false },
                    { label: 'Dax', data: daxData, borderColor: '#ff9900', tension: 0.2, fill: false }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#00f5d4', font: { family: 'Courier New' } } },
                    y: { ticks: { color: '#00f5d4', font: { family: 'Courier New' } } }
                }
            }
        });
    </script>
</body>
</html>
