from simulai.core.world import World
from simulai.environment.grid import Grid


def test_metrics_export_creates_csv(tmp_path):
    output_file = tmp_path / "metrics.csv"

    world = World(Grid(5, 5))
    world.metrics_exporter.output_path = output_file
    world.metrics_exporter.overwrite = False

    world.step()

    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "tick,population,births,deaths,max_generation,trend,weather" in content
    assert "1," in content
