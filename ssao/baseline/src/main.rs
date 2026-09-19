#[global_allocator]
static GLOBAL: mimalloc::MiMalloc = mimalloc::MiMalloc;

use std::sync::Arc;

use glam::{Mat4, Quat, Vec3};
use wgpu::util::DeviceExt;
use winit::{
    application::ApplicationHandler,
    dpi::PhysicalSize,
    event::WindowEvent,
    event_loop::{ActiveEventLoop, ControlFlow, EventLoop},
    window::{Window, WindowId},
};

const WIDTH: u32 = 1920;
const HEIGHT: u32 = 1080;

const GBUFFER_FORMAT: wgpu::TextureFormat = wgpu::TextureFormat::Rgba16Float;
const DEPTH_FORMAT: wgpu::TextureFormat = wgpu::TextureFormat::Depth32Float;

const CAMERA_POSITION: Vec3 = Vec3::new(3.5, 2.0, -3.0000002);
const CAMERA_YAW: f32 = 2.5213435;
const CAMERA_PITCH: f32 = -0.33555448;
const CAMERA_FOVY: f32 = 1.0471976;
const CAMERA_ZNEAR: f32 = 0.1;
const CAMERA_ZFAR: f32 = 100.0;

const BACKPACK_POSITION: Vec3 = Vec3::new(0.0, 0.5, 0.0);
const BACKPACK_ROTATION: Vec3 = Vec3::new(-90.0, 0.0, 0.0);

const SSAO_RADIUS: f32 = 0.5;
const SSAO_BIAS: f32 = 0.025;
const SSAO_POWER: f32 = 1.5;
const SSAO_KERNEL_SIZE: u32 = 8;

const LIGHT_POSITION: Vec3 = Vec3::new(2.0, 4.0, -2.0);
const LIGHT_COLOR: Vec3 = Vec3::new(0.9, 0.2, 0.2);
const LIGHT_LINEAR: f32 = 0.09;
const LIGHT_QUADRATIC: f32 = 0.032;

const MODEL_STRIDE: wgpu::BufferAddress = 14 * 4;
const MODEL_ATTRIBUTES: [wgpu::VertexAttribute; 5] = wgpu::vertex_attr_array![
    0 => Float32x3,
    1 => Float32x2,
    2 => Float32x3,
    3 => Float32x3,
    4 => Float32x3,
];

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct CameraUniform {
    position: [f32; 4],
    view: [[f32; 4]; 4],
    projection: [[f32; 4]; 4],
    projection_view: [[f32; 4]; 4],
}

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct TransformUniform {
    model: [[f32; 4]; 4],
}

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct SsaoUniform {
    radius: f32,
    bias: f32,
    power: f32,
    kernel_size: u32,
}

#[repr(C)]
#[derive(Clone, Copy, bytemuck::Pod, bytemuck::Zeroable)]
struct LightUniform {
    position: [f32; 3],
    _pad0: f32,
    color: [f32; 3],
    linear: f32,
    quadratic: f32,
    _pad1: [f32; 3],
}

struct Mesh {
    vertices: wgpu::Buffer,
    indices: wgpu::Buffer,
    index_count: u32,
}

struct State {
    window: Arc<Window>,
    surface: wgpu::Surface<'static>,
    device: wgpu::Device,
    queue: wgpu::Queue,
    config: wgpu::SurfaceConfiguration,

    gbuffer_position: wgpu::TextureView,
    gbuffer_normal: wgpu::TextureView,
    gbuffer_depth: wgpu::TextureView,
    ssao_raw: wgpu::TextureView,
    ssao_blurred: wgpu::TextureView,

    camera_bind_group: wgpu::BindGroup,
    transform_bind_group: wgpu::BindGroup,
    ssao_params_bind_group: wgpu::BindGroup,
    light_bind_group: wgpu::BindGroup,
    gbuffer_sample_bind_group: wgpu::BindGroup,
    blur_sample_bind_group: wgpu::BindGroup,
    lighting_sample_bind_group: wgpu::BindGroup,

    room_pipeline: wgpu::RenderPipeline,
    backpack_pipeline: wgpu::RenderPipeline,
    ssao_pipeline: wgpu::RenderPipeline,
    blur_pipeline: wgpu::RenderPipeline,
    lighting_pipeline: wgpu::RenderPipeline,

    meshes: Vec<Mesh>,
}

fn render_target(
    device: &wgpu::Device,
    label: &str,
    format: wgpu::TextureFormat,
    usage: wgpu::TextureUsages,
) -> wgpu::TextureView {
    let texture = device.create_texture(&wgpu::TextureDescriptor {
        label: Some(label),
        size: wgpu::Extent3d {
            width: WIDTH,
            height: HEIGHT,
            depth_or_array_layers: 1,
        },
        mip_level_count: 1,
        sample_count: 1,
        dimension: wgpu::TextureDimension::D2,
        format,
        usage,
        view_formats: &[],
    });

    texture.create_view(&wgpu::TextureViewDescriptor::default())
}

fn uniform_layout(device: &wgpu::Device, label: &str) -> wgpu::BindGroupLayout {
    device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
        label: Some(label),
        entries: &[wgpu::BindGroupLayoutEntry {
            binding: 0,
            visibility: wgpu::ShaderStages::VERTEX_FRAGMENT,
            ty: wgpu::BindingType::Buffer {
                ty: wgpu::BufferBindingType::Uniform,
                has_dynamic_offset: false,
                min_binding_size: None,
            },
            count: None,
        }],
    })
}

fn uniform_bind_group<T: bytemuck::Pod>(
    device: &wgpu::Device,
    label: &str,
    layout: &wgpu::BindGroupLayout,
    value: T,
) -> wgpu::BindGroup {
    let buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some(label),
        contents: bytemuck::bytes_of(&value),
        usage: wgpu::BufferUsages::UNIFORM,
    });

    device.create_bind_group(&wgpu::BindGroupDescriptor {
        label: Some(label),
        layout,
        entries: &[wgpu::BindGroupEntry {
            binding: 0,
            resource: buffer.as_entire_binding(),
        }],
    })
}

fn sample_layout(device: &wgpu::Device, label: &str, textures: u32) -> wgpu::BindGroupLayout {
    let mut entries: Vec<wgpu::BindGroupLayoutEntry> = (0..textures)
        .map(|binding| wgpu::BindGroupLayoutEntry {
            binding,
            visibility: wgpu::ShaderStages::VERTEX_FRAGMENT,
            ty: wgpu::BindingType::Texture {
                sample_type: wgpu::TextureSampleType::Float { filterable: false },
                view_dimension: wgpu::TextureViewDimension::D2,
                multisampled: false,
            },
            count: None,
        })
        .collect();

    entries.push(wgpu::BindGroupLayoutEntry {
        binding: textures,
        visibility: wgpu::ShaderStages::VERTEX_FRAGMENT,
        ty: wgpu::BindingType::Sampler(wgpu::SamplerBindingType::NonFiltering),
        count: None,
    });

    device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
        label: Some(label),
        entries: &entries,
    })
}

fn sample_bind_group(
    device: &wgpu::Device,
    label: &str,
    layout: &wgpu::BindGroupLayout,
    views: &[&wgpu::TextureView],
    sampler: &wgpu::Sampler,
) -> wgpu::BindGroup {
    let mut entries: Vec<wgpu::BindGroupEntry> = views
        .iter()
        .enumerate()
        .map(|(binding, view)| wgpu::BindGroupEntry {
            binding: binding as u32,
            resource: wgpu::BindingResource::TextureView(view),
        })
        .collect();

    entries.push(wgpu::BindGroupEntry {
        binding: views.len() as u32,
        resource: wgpu::BindingResource::Sampler(sampler),
    });

    device.create_bind_group(&wgpu::BindGroupDescriptor {
        label: Some(label),
        layout,
        entries: &entries,
    })
}

fn pipeline(
    device: &wgpu::Device,
    label: &str,
    shader: &wgpu::ShaderModule,
    layouts: &[Option<&wgpu::BindGroupLayout>],
    buffers: &[Option<wgpu::VertexBufferLayout>],
    formats: &[wgpu::TextureFormat],
    depth: bool,
) -> wgpu::RenderPipeline {
    let layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
        label: Some(label),
        bind_group_layouts: layouts,
        immediate_size: 0,
    });

    let targets: Vec<Option<wgpu::ColorTargetState>> = formats
        .iter()
        .map(|format| {
            Some(wgpu::ColorTargetState {
                format: *format,
                blend: Some(wgpu::BlendState::REPLACE),
                write_mask: wgpu::ColorWrites::ALL,
            })
        })
        .collect();

    device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
        label: Some(label),
        layout: Some(&layout),
        vertex: wgpu::VertexState {
            module: shader,
            entry_point: Some("vs_main"),
            compilation_options: Default::default(),
            buffers,
        },
        primitive: wgpu::PrimitiveState::default(),
        depth_stencil: depth.then(|| wgpu::DepthStencilState {
            format: DEPTH_FORMAT,
            depth_write_enabled: Some(true),
            depth_compare: Some(wgpu::CompareFunction::LessEqual),
            stencil: wgpu::StencilState::default(),
            bias: wgpu::DepthBiasState::default(),
        }),
        multisample: wgpu::MultisampleState::default(),
        fragment: Some(wgpu::FragmentState {
            module: shader,
            entry_point: Some("fs_main"),
            compilation_options: Default::default(),
            targets: &targets,
        }),
        multiview_mask: None,
        cache: None,
    })
}

fn load_backpack(device: &wgpu::Device) -> Vec<Mesh> {
    let obj = include_bytes!("../../backpack.obj");

    let (models, _) = tobj::load_obj_buf(
        &mut std::io::Cursor::new(obj.as_slice()),
        &tobj::LoadOptions {
            triangulate: true,
            single_index: true,
            ..Default::default()
        },
        |_| Ok((Vec::new(), Default::default())),
    )
    .expect("failed to load backpack.obj");

    models
        .iter()
        .map(|model| {
            let mesh = &model.mesh;
            let vertex_count = mesh.positions.len() / 3;

            let mut vertices = Vec::with_capacity(vertex_count * 14);
            for i in 0..vertex_count {
                vertices.extend_from_slice(&mesh.positions[i * 3..i * 3 + 3]);
                vertices.extend_from_slice(
                    mesh.texcoords
                        .get(i * 2..i * 2 + 2)
                        .unwrap_or(&[0.0f32, 0.0]),
                );
                vertices.extend_from_slice(
                    mesh.normals
                        .get(i * 3..i * 3 + 3)
                        .unwrap_or(&[0.0f32, 0.0, 0.0]),
                );
                vertices.extend_from_slice(&[0.0f32; 6]);
            }

            Mesh {
                vertices: device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
                    label: Some("Backpack Vertices"),
                    contents: bytemuck::cast_slice(&vertices),
                    usage: wgpu::BufferUsages::VERTEX,
                }),
                indices: device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
                    label: Some("Backpack Indices"),
                    contents: bytemuck::cast_slice(&mesh.indices),
                    usage: wgpu::BufferUsages::INDEX,
                }),
                index_count: mesh.indices.len() as u32,
            }
        })
        .collect()
}

fn camera_uniform() -> CameraUniform {
    let (yaw_sin, yaw_cos) = CAMERA_YAW.sin_cos();
    let (pitch_sin, pitch_cos) = CAMERA_PITCH.sin_cos();
    let direction = Vec3::new(pitch_cos * yaw_cos, pitch_sin, pitch_cos * yaw_sin);

    let view =
        glam::camera::rh::view::look_at_mat4(CAMERA_POSITION, CAMERA_POSITION + direction, Vec3::Y);
    let projection = glam::camera::rh::proj::directx::perspective(
        CAMERA_FOVY,
        WIDTH as f32 / HEIGHT as f32,
        CAMERA_ZNEAR,
        CAMERA_ZFAR,
    );

    CameraUniform {
        position: CAMERA_POSITION.extend(1.0).to_array(),
        view: view.to_cols_array_2d(),
        projection: projection.to_cols_array_2d(),
        projection_view: (projection * view).to_cols_array_2d(),
    }
}

impl State {
    fn new(window: Arc<Window>) -> Self {
        let instance = wgpu::Instance::new(wgpu::InstanceDescriptor {
            backends: wgpu::Backends::DX12,
            ..wgpu::InstanceDescriptor::new_without_display_handle()
        });

        let surface = instance.create_surface(window.clone()).unwrap();

        let adapter = pollster::block_on(instance.request_adapter(&wgpu::RequestAdapterOptions {
            power_preference: wgpu::PowerPreference::HighPerformance,
            compatible_surface: Some(&surface),
            ..Default::default()
        }))
        .unwrap();

        let (device, queue) =
            pollster::block_on(adapter.request_device(&wgpu::DeviceDescriptor::default())).unwrap();

        let size = window.inner_size();
        let mut config = surface
            .get_default_config(&adapter, size.width.max(1), size.height.max(1))
            .unwrap();
        config.present_mode = wgpu::PresentMode::AutoNoVsync;
        config.format = surface
            .get_capabilities(&adapter)
            .formats
            .iter()
            .copied()
            .find(|format| format.is_srgb())
            .unwrap_or(config.format);
        surface.configure(&device, &config);

        let attachment =
            wgpu::TextureUsages::TEXTURE_BINDING | wgpu::TextureUsages::RENDER_ATTACHMENT;
        let gbuffer_position =
            render_target(&device, "G-Buffer Position", GBUFFER_FORMAT, attachment);
        let gbuffer_normal = render_target(&device, "G-Buffer Normal", GBUFFER_FORMAT, attachment);
        let gbuffer_depth = render_target(
            &device,
            "G-Buffer Depth",
            DEPTH_FORMAT,
            wgpu::TextureUsages::RENDER_ATTACHMENT,
        );
        let ssao_raw = render_target(&device, "SSAO Raw", GBUFFER_FORMAT, attachment);
        let ssao_blurred = render_target(&device, "SSAO Blurred", GBUFFER_FORMAT, attachment);

        let sampler = device.create_sampler(&wgpu::SamplerDescriptor {
            label: Some("G-Buffer Sampler"),
            address_mode_u: wgpu::AddressMode::ClampToEdge,
            address_mode_v: wgpu::AddressMode::ClampToEdge,
            address_mode_w: wgpu::AddressMode::ClampToEdge,
            mag_filter: wgpu::FilterMode::Nearest,
            min_filter: wgpu::FilterMode::Nearest,
            mipmap_filter: wgpu::MipmapFilterMode::Nearest,
            lod_min_clamp: 0.0,
            lod_max_clamp: 32.0,
            compare: None,
            anisotropy_clamp: 1,
            border_color: None,
        });

        let camera_layout = uniform_layout(&device, "Camera");
        let transform_layout = uniform_layout(&device, "Backpack Transform");
        let ssao_params_layout = uniform_layout(&device, "SSAO Params");
        let light_layout = uniform_layout(&device, "Point Light");
        let gbuffer_sample_layout = sample_layout(&device, "G-Buffer Sample", 2);
        let blur_sample_layout = sample_layout(&device, "Blur Sample", 1);
        let lighting_sample_layout = sample_layout(&device, "Lighting Sample", 3);

        let camera_bind_group =
            uniform_bind_group(&device, "Camera", &camera_layout, camera_uniform());

        let model = Mat4::from_scale_rotation_translation(
            Vec3::ONE,
            Quat::from_euler(
                glam::EulerRot::XYZ,
                BACKPACK_ROTATION.x.to_radians(),
                BACKPACK_ROTATION.y.to_radians(),
                BACKPACK_ROTATION.z.to_radians(),
            ),
            BACKPACK_POSITION,
        );
        let transform_bind_group = uniform_bind_group(
            &device,
            "Backpack Transform",
            &transform_layout,
            TransformUniform {
                model: model.to_cols_array_2d(),
            },
        );

        let ssao_params_bind_group = uniform_bind_group(
            &device,
            "SSAO Params",
            &ssao_params_layout,
            SsaoUniform {
                radius: SSAO_RADIUS,
                bias: SSAO_BIAS,
                power: SSAO_POWER,
                kernel_size: SSAO_KERNEL_SIZE,
            },
        );

        let light_bind_group = uniform_bind_group(
            &device,
            "Point Light",
            &light_layout,
            LightUniform {
                position: LIGHT_POSITION.to_array(),
                _pad0: 0.0,
                color: LIGHT_COLOR.to_array(),
                linear: LIGHT_LINEAR,
                quadratic: LIGHT_QUADRATIC,
                _pad1: [0.0; 3],
            },
        );

        let gbuffer_sample_bind_group = sample_bind_group(
            &device,
            "G-Buffer Sample",
            &gbuffer_sample_layout,
            &[&gbuffer_position, &gbuffer_normal],
            &sampler,
        );
        let blur_sample_bind_group = sample_bind_group(
            &device,
            "Blur Sample",
            &blur_sample_layout,
            &[&ssao_raw],
            &sampler,
        );
        let lighting_sample_bind_group = sample_bind_group(
            &device,
            "Lighting Sample",
            &lighting_sample_layout,
            &[&gbuffer_position, &gbuffer_normal, &ssao_blurred],
            &sampler,
        );

        let shader = |label: &str, source: &str| {
            device.create_shader_module(wgpu::ShaderModuleDescriptor {
                label: Some(label),
                source: wgpu::ShaderSource::Wgsl(source.into()),
            })
        };

        let room_shader = shader(
            "Room G-Buffer",
            include_str!("../../rau/project/room_gbuffer.wgsl"),
        );
        let backpack_shader = shader(
            "Backpack G-Buffer",
            include_str!("../../rau/project/backpack_gbuffer.wgsl"),
        );
        let ssao_shader = shader("SSAO", include_str!("../../rau/project/ssao.wgsl"));
        let blur_shader = shader("SSAO Blur", include_str!("../../rau/project/blur.wgsl"));
        let lighting_shader = shader("Lighting", include_str!("../../rau/project/lighting.wgsl"));

        let room_pipeline = pipeline(
            &device,
            "Room G-Buffer Pipeline",
            &room_shader,
            &[Some(&camera_layout)],
            &[],
            &[GBUFFER_FORMAT, GBUFFER_FORMAT],
            true,
        );
        let backpack_pipeline = pipeline(
            &device,
            "Backpack G-Buffer Pipeline",
            &backpack_shader,
            &[Some(&camera_layout), Some(&transform_layout)],
            &[Some(wgpu::VertexBufferLayout {
                array_stride: MODEL_STRIDE,
                step_mode: wgpu::VertexStepMode::Vertex,
                attributes: &MODEL_ATTRIBUTES,
            })],
            &[GBUFFER_FORMAT, GBUFFER_FORMAT],
            true,
        );
        let ssao_pipeline = pipeline(
            &device,
            "SSAO Pipeline",
            &ssao_shader,
            &[
                Some(&camera_layout),
                Some(&gbuffer_sample_layout),
                Some(&ssao_params_layout),
            ],
            &[],
            &[GBUFFER_FORMAT],
            false,
        );
        let blur_pipeline = pipeline(
            &device,
            "SSAO Blur Pipeline",
            &blur_shader,
            &[Some(&blur_sample_layout)],
            &[],
            &[GBUFFER_FORMAT],
            false,
        );
        let lighting_pipeline = pipeline(
            &device,
            "Lighting Pipeline",
            &lighting_shader,
            &[
                Some(&camera_layout),
                Some(&light_layout),
                Some(&lighting_sample_layout),
            ],
            &[],
            &[config.format],
            false,
        );

        let meshes = load_backpack(&device);

        Self {
            window,
            surface,
            device,
            queue,
            config,
            gbuffer_position,
            gbuffer_normal,
            gbuffer_depth,
            ssao_raw,
            ssao_blurred,
            camera_bind_group,
            transform_bind_group,
            ssao_params_bind_group,
            light_bind_group,
            gbuffer_sample_bind_group,
            blur_sample_bind_group,
            lighting_sample_bind_group,
            room_pipeline,
            backpack_pipeline,
            ssao_pipeline,
            blur_pipeline,
            lighting_pipeline,
            meshes,
        }
    }

    fn resize(&mut self, size: PhysicalSize<u32>) {
        if size.width == 0 || size.height == 0 {
            return;
        }

        self.config.width = size.width;
        self.config.height = size.height;
        self.surface.configure(&self.device, &self.config);
    }

    fn render(&mut self) {
        let frame = match self.surface.get_current_texture() {
            wgpu::CurrentSurfaceTexture::Success(frame)
            | wgpu::CurrentSurfaceTexture::Suboptimal(frame) => frame,
            _ => {
                self.surface.configure(&self.device, &self.config);
                return;
            }
        };

        let target = frame
            .texture
            .create_view(&wgpu::TextureViewDescriptor::default());

        let mut encoder = self
            .device
            .create_command_encoder(&wgpu::CommandEncoderDescriptor::default());

        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("G-Buffer Pass"),
                color_attachments: &[
                    Some(color_attachment(
                        &self.gbuffer_position,
                        wgpu::Color::TRANSPARENT,
                    )),
                    Some(color_attachment(
                        &self.gbuffer_normal,
                        wgpu::Color::TRANSPARENT,
                    )),
                ],
                depth_stencil_attachment: Some(wgpu::RenderPassDepthStencilAttachment {
                    view: &self.gbuffer_depth,
                    depth_ops: Some(wgpu::Operations {
                        load: wgpu::LoadOp::Clear(1.0),
                        store: wgpu::StoreOp::Store,
                    }),
                    stencil_ops: None,
                }),
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });

            pass.set_pipeline(&self.room_pipeline);
            pass.set_bind_group(0, &self.camera_bind_group, &[]);
            pass.draw(0..36, 0..1);

            pass.set_pipeline(&self.backpack_pipeline);
            pass.set_bind_group(0, &self.camera_bind_group, &[]);
            pass.set_bind_group(1, &self.transform_bind_group, &[]);
            for mesh in &self.meshes {
                pass.set_vertex_buffer(0, mesh.vertices.slice(..));
                pass.set_index_buffer(mesh.indices.slice(..), wgpu::IndexFormat::Uint32);
                pass.draw_indexed(0..mesh.index_count, 0, 0..1);
            }
        }

        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("SSAO Pass"),
                color_attachments: &[Some(color_attachment(&self.ssao_raw, wgpu::Color::WHITE))],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });

            pass.set_pipeline(&self.ssao_pipeline);
            pass.set_bind_group(0, &self.camera_bind_group, &[]);
            pass.set_bind_group(1, &self.gbuffer_sample_bind_group, &[]);
            pass.set_bind_group(2, &self.ssao_params_bind_group, &[]);
            pass.draw(0..3, 0..1);
        }

        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("SSAO Blur Pass"),
                color_attachments: &[Some(color_attachment(
                    &self.ssao_blurred,
                    wgpu::Color::WHITE,
                ))],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });

            pass.set_pipeline(&self.blur_pipeline);
            pass.set_bind_group(0, &self.blur_sample_bind_group, &[]);
            pass.draw(0..3, 0..1);
        }

        {
            let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
                label: Some("Lighting Pass"),
                color_attachments: &[Some(color_attachment(
                    &target,
                    wgpu::Color {
                        r: 0.05,
                        g: 0.05,
                        b: 0.05,
                        a: 1.0,
                    },
                ))],
                depth_stencil_attachment: None,
                timestamp_writes: None,
                occlusion_query_set: None,
                multiview_mask: None,
            });

            pass.set_pipeline(&self.lighting_pipeline);
            pass.set_bind_group(0, &self.camera_bind_group, &[]);
            pass.set_bind_group(1, &self.light_bind_group, &[]);
            pass.set_bind_group(2, &self.lighting_sample_bind_group, &[]);
            pass.draw(0..3, 0..1);
        }

        self.queue.submit([encoder.finish()]);
        self.window.pre_present_notify();
        self.queue.present(frame);
    }
}

fn color_attachment(
    view: &wgpu::TextureView,
    clear: wgpu::Color,
) -> wgpu::RenderPassColorAttachment<'_> {
    wgpu::RenderPassColorAttachment {
        view,
        depth_slice: None,
        resolve_target: None,
        ops: wgpu::Operations {
            load: wgpu::LoadOp::Clear(clear),
            store: wgpu::StoreOp::Store,
        },
    }
}

#[derive(Default)]
struct App {
    state: Option<State>,
}

impl ApplicationHandler for App {
    fn resumed(&mut self, event_loop: &ActiveEventLoop) {
        if self.state.is_some() {
            return;
        }

        let attributes = Window::default_attributes()
            .with_title("SSAO Baseline")
            .with_inner_size(PhysicalSize::new(WIDTH, HEIGHT))
            .with_resizable(false);

        let window = Arc::new(event_loop.create_window(attributes).unwrap());
        self.state = Some(State::new(window));
    }

    fn window_event(&mut self, event_loop: &ActiveEventLoop, _: WindowId, event: WindowEvent) {
        let Some(state) = self.state.as_mut() else {
            return;
        };

        match event {
            WindowEvent::CloseRequested => event_loop.exit(),
            WindowEvent::Resized(size) => state.resize(size),
            WindowEvent::RedrawRequested => {
                state.render();
                state.window.request_redraw();
            }
            _ => {}
        }
    }
}

fn main() {
    let event_loop = EventLoop::new().unwrap();
    event_loop.set_control_flow(ControlFlow::Poll);
    event_loop.run_app(&mut App::default()).unwrap();
}
