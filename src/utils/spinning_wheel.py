# Create and animate spinning wheel
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import random
import time
import streamlit as st


class SpinningWheel:
    def __init__(self):
        self.plot_placeholder = None


    def create_frames_and_plot(self, values, num_segments):
        # Create the initial pie chart
        fig = go.Figure()
        colors = plt.cm.rainbow(np.linspace(0, 1, num_segments))
        colors = [tuple(c) for c in colors]

        # Add the initial pie chart
        fig.add_trace(
            go.Pie(
                labels=values,
                textinfo="label",
                hoverinfo="label",
                marker=dict(colors=colors, line=dict(width=0)),
                textfont=dict(size=5),
                showlegend=False,
                hole=0.05,
                sort=False,  # Disable sorting to keep fixed positions
                direction="clockwise",
            )
        )

        # Set the initial rotation angle
        max_rotation_angle = (lambda x: x + 1 if x % (360 // num_segments) == 0 else x)(
            random.randint(0, 1080) + 1080
        )

        # Create frames for the animation with a decelerating effect
        frames = []
        total_frames = 100
        for i in range(total_frames):
            t = i / total_frames  # Normalize the frame index to [0, 1]

            # Apply the easing function (deceleration) to the rotation angle
            angle = (1 - (1 - t) ** 3) * max_rotation_angle

            frames.append(
                go.Frame(
                    data=[
                        go.Pie(
                            labels=values,
                            textinfo="label",
                            hoverinfo="label",
                            marker=dict(colors=colors, line=dict(width=0)),
                            sort=False,
                            hole=0.05,
                            direction="clockwise",
                            textfont=dict(size=5),
                            showlegend=False,
                            rotation=angle,  # Apply the new rotation angle
                        )
                    ]
                )
            )

        # Update the layout to support frames and add the play button
        fig.frames = frames

        # Add an annotation to simulate the pointer/arrow at the top
        fig.add_annotation(
            x=0.5,
            y=1.03,
            showarrow=False,
            text="▼",
            font=dict(size=20, color="black"),
            xref="paper",
            yref="paper",
        )

        return fig, frames, max_rotation_angle


    def add_pointer_to_figure(self, fig):
        fig.add_annotation(
            x=0.5,
            y=1.03,
            showarrow=False,
            text="▼",
            font=dict(size=20, color="black"),
            xref="paper",
            yref="paper",
        )


    def initialize_wheel(self, topics, num_topics):
        # Create the animated plot
        fig, frames, final_angle = self.create_frames_and_plot(topics, num_topics)
        # Display the plotly figure
        self.plot_placeholder = st.empty()
        self.plot_placeholder.plotly_chart(fig, config={"displayModeBar": False})
        return frames, final_angle


    def animate_spin(self, frames):
        for frame in frames:
            fig = go.Figure(data=frame.data)
            self.add_pointer_to_figure(fig)
            self.plot_placeholder.plotly_chart(
                fig, config={"displayModeBar": False}
            )
            time.sleep(0.03)