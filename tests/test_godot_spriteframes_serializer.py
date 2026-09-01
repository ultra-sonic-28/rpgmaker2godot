from rpgmaker2godot.godot.spriteframes.models import (
    GodotSpriteFramesAnimation,
    GodotSpriteFramesFrame,
    GodotSpriteFramesResource,
    GodotSpriteFramesTexture,
)
from rpgmaker2godot.godot.spriteframes.serializer import (
    GodotSpriteFramesSerializer,
)


def build_resource() -> GodotSpriteFramesResource:
    texture = GodotSpriteFramesTexture(
        resource_id="1_texture",
        resource_type="Texture2D",
        path="res://player-1.png",
    )

    return GodotSpriteFramesResource(
        texture=texture,
        animations=(
            GodotSpriteFramesAnimation(
                name="idle-down",
                speed=2.0,
                loop=True,
                frames=(
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_1",
                        x=0,
                        y=192,
                        width=48,
                        height=48,
                    ),
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_2",
                        x=48,
                        y=192,
                        width=48,
                        height=48,
                    ),
                ),
            ),
            GodotSpriteFramesAnimation(
                name="damaged",
                speed=8.0,
                loop=False,
                frames=(
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_3",
                        x=0,
                        y=384,
                        width=48,
                        height=48,
                    ),
                ),
            ),
        ),
    )


def test_serializes_the_resource_header() -> None:
    content = GodotSpriteFramesSerializer().serialize(build_resource())

    assert (
        '[gd_resource type="SpriteFrames" load_steps=5 format=3]'
        in content
    )
    assert (
        '[ext_resource type="Texture2D" '
        'path="res://player-1.png" id="1_texture"]'
        in content
    )


def test_serializes_every_frame_as_an_atlas_texture() -> None:
    content = GodotSpriteFramesSerializer().serialize(build_resource())

    assert (
        '[sub_resource type="AtlasTexture" id="AtlasTexture_1"]'
        in content
    )
    assert 'atlas = ExtResource("1_texture")' in content
    assert "region = Rect2(0, 192, 48, 48)" in content
    assert "region = Rect2(48, 192, 48, 48)" in content
    assert "region = Rect2(0, 384, 48, 48)" in content


def test_serializes_the_animations_array() -> None:
    content = GodotSpriteFramesSerializer().serialize(build_resource())

    assert '"loop": true,' in content
    assert '"loop": false,' in content
    assert '"name": &"idle-down",' in content
    assert '"name": &"damaged",' in content
    assert '"speed": 2.0' in content
    assert '"speed": 8.0' in content
    assert '"duration": 1.0,' in content
    assert 'SubResource("AtlasTexture_1")' in content

    # Multi-entry arrays mirror Godot's own multi-line style.
    assert "}, {" in content
    assert content.endswith("}]\n")


def test_load_steps_counts_ext_and_sub_resources() -> None:
    # 3 AtlasTexture sub-resources + 1 ext_resource + the resource.
    content = GodotSpriteFramesSerializer().serialize(build_resource())

    assert "load_steps=5" in content


def test_uses_each_animation_duration() -> None:
    resource = GodotSpriteFramesResource(
        texture=GodotSpriteFramesTexture(
            resource_id="1_texture",
            resource_type="Texture2D",
            path="res://hero.png",
        ),
        animations=(
            GodotSpriteFramesAnimation(
                name="idle-down",
                speed=3.0,
                loop=True,
                duration=0.5,
                frames=(
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_1",
                        x=0,
                        y=192,
                        width=48,
                        height=48,
                    ),
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_2",
                        x=48,
                        y=192,
                        width=48,
                        height=48,
                    ),
                ),
            ),
            GodotSpriteFramesAnimation(
                name="damaged",
                speed=5.0,
                loop=False,
                duration=0.25,
                frames=(
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_3",
                        x=0,
                        y=384,
                        width=48,
                        height=48,
                    ),
                ),
            ),
        ),
    )

    content = GodotSpriteFramesSerializer().serialize(resource)

    assert '"duration": 0.5,' in content
    assert '"duration": 0.25,' in content
    assert '"duration": 1.0,' not in content


def test_full_output_for_a_single_frame_animation() -> None:
    resource = GodotSpriteFramesResource(
        texture=GodotSpriteFramesTexture(
            resource_id="1_texture",
            resource_type="Texture2D",
            path="res://hero.png",
        ),
        animations=(
            GodotSpriteFramesAnimation(
                name="idle-down",
                speed=2.0,
                loop=True,
                frames=(
                    GodotSpriteFramesFrame(
                        resource_id="AtlasTexture_1",
                        x=0,
                        y=0,
                        width=48,
                        height=48,
                    ),
                ),
            ),
        ),
    )

    content = GodotSpriteFramesSerializer().serialize(resource)

    assert content == (
        '[gd_resource type="SpriteFrames" load_steps=3 format=3]\n'
        "\n"
        '[ext_resource type="Texture2D" '
        'path="res://hero.png" id="1_texture"]\n'
        "\n"
        '[sub_resource type="AtlasTexture" id="AtlasTexture_1"]\n'
        'atlas = ExtResource("1_texture")\n'
        "region = Rect2(0, 0, 48, 48)\n"
        "\n"
        "[resource]\n"
        "animations = [{\n"
        '"frames": [{\n'
        '"duration": 1.0,\n'
        '"texture": SubResource("AtlasTexture_1")\n'
        "}],\n"
        '"loop": true,\n'
        '"name": &"idle-down",\n'
        '"speed": 2.0\n'
        "}]\n"
    )
