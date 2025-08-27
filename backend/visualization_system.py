#!/usr/bin/env python3
"""
Visualization System for Deer Prediction

This module handles all visualization tasks including:
- Heatmap generation
- Terrain visualization
- Score distribution plots
- Feature overlay maps

Key Features:
- Consistent color schemes
- Clear visual indicators
- Explanatory annotations
- Performance optimization
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class VisualizationConfig:
    """Configuration for visualization settings"""
    colormap: str = 'RdYlBu_r'
    figure_size: tuple = (10, 8)
    dpi: int = 150
    title_fontsize: int = 14
    label_fontsize: int = 11
    annotation_fontsize: int = 10
    grid_alpha: float = 0.3
    contour_levels: int = 11

class VisualizationSystem:
    """Central visualization system for deer prediction"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualization system with configuration"""
        self.config = config or VisualizationConfig()
        
    def create_score_heatmap(self, score_grid: np.ndarray,
                            title: str,
                            description: str) -> str:
        """Create an enhanced score heatmap with clear visual indicators"""
        try:
            fig, ax = plt.subplots(figsize=self.config.figure_size)
            
            # Normalize and enhance scores
            normalized_scores = self._normalize_score_grid(score_grid)
            levels = self._determine_contour_levels(normalized_scores)
            
            # Create enhanced heatmap
            im = ax.contourf(normalized_scores,
                            levels=levels,
                            cmap=self.config.colormap,
                            extend='both')
            
            # Add and configure colorbar
            cbar = self._add_enhanced_colorbar(fig, ax, im, normalized_scores)
            
            # Enhance plot appearance
            self._enhance_plot_appearance(ax, title, description)
            
            # Add statistics
            self._add_score_statistics(ax, score_grid)
            
            # Add grid and finalize
            ax.grid(True, alpha=self.config.grid_alpha)
            
            # Convert to base64
            return self._figure_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error creating score heatmap: {e}")
            return self._create_error_visualization()
        finally:
            plt.close()

    def create_terrain_visualization(self, elevation_grid: np.ndarray,
                                   features: Dict[str, Any],
                                   score_overlay: Optional[np.ndarray] = None) -> str:
        """Create terrain visualization with feature overlay"""
        try:
            fig = plt.figure(figsize=self.config.figure_size)
            ax = fig.add_subplot(111, projection='3d')
            
            # Create terrain surface
            x, y = np.meshgrid(range(elevation_grid.shape[1]),
                             range(elevation_grid.shape[0]))
            
            # Plot terrain surface
            surf = ax.plot_surface(x, y, elevation_grid,
                                 cmap='terrain',
                                 alpha=0.7)
            
            # Add score overlay if provided
            if score_overlay is not None:
                score_colors = plt.cm.RdYlBu_r(score_overlay / 10.0)
                ax.plot_surface(x, y, elevation_grid,
                              facecolors=score_colors,
                              alpha=0.3)
            
            # Add feature markers
            self._add_feature_markers(ax, features, elevation_grid)
            
            # Configure 3D view
            ax.view_init(elev=45, azim=45)
            ax.set_title("Terrain Analysis with Features",
                        fontsize=self.config.title_fontsize)
            
            # Add colorbar
            fig.colorbar(surf, ax=ax, shrink=0.5, label='Elevation (m)')
            
            return self._figure_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error creating terrain visualization: {e}")
            return self._create_error_visualization()
        finally:
            plt.close()

    def create_score_distribution(self, scores: np.ndarray,
                                title: str = "Score Distribution") -> str:
        """Create score distribution visualization"""
        try:
            fig, ax = plt.subplots(figsize=self.config.figure_size)
            
            # Create enhanced histogram
            bins = np.linspace(0, 10, 21)
            n, bins, patches = ax.hist(scores.flatten(),
                                     bins=bins,
                                     edgecolor='black')
            
            # Color bars by score value
            cm = plt.cm.get_cmap(self.config.colormap)
            for i, p in enumerate(patches):
                p.set_facecolor(cm(i / len(patches)))
            
            # Add statistics
            mean_score = np.mean(scores)
            median_score = np.median(scores)
            
            stats_text = (f"Mean: {mean_score:.1f}\n"
                         f"Median: {median_score:.1f}\n"
                         f"High Scores (>7): {np.sum(scores > 7) / scores.size:.1%}")
            
            ax.text(0.02, 0.98, stats_text,
                   transform=ax.transAxes,
                   verticalalignment='top',
                   bbox=dict(boxstyle='round',
                            facecolor='white',
                            alpha=0.8))
            
            # Enhance appearance
            ax.set_title(title, fontsize=self.config.title_fontsize)
            ax.set_xlabel("Score", fontsize=self.config.label_fontsize)
            ax.set_ylabel("Frequency", fontsize=self.config.label_fontsize)
            ax.grid(True, alpha=self.config.grid_alpha)
            
            return self._figure_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error creating score distribution: {e}")
            return self._create_error_visualization()
        finally:
            plt.close()

    def create_feature_map(self, features: Dict[str, Any],
                         base_grid: np.ndarray,
                         title: str = "Terrain Features") -> str:
        """Create feature map visualization"""
        try:
            fig, ax = plt.subplots(figsize=self.config.figure_size)
            
            # Plot base grid
            im = ax.imshow(base_grid, cmap='terrain', alpha=0.5)
            
            # Add feature markers with different colors and symbols
            self._plot_features(ax, features)
            
            # Add legend
            self._add_feature_legend(ax)
            
            # Enhance appearance
            ax.set_title(title, fontsize=self.config.title_fontsize)
            ax.grid(True, alpha=self.config.grid_alpha)
            
            # Add colorbar for base grid
            fig.colorbar(im, ax=ax, label='Elevation (m)')
            
            return self._figure_to_base64(fig)
            
        except Exception as e:
            logger.error(f"Error creating feature map: {e}")
            return self._create_error_visualization()
        finally:
            plt.close()

    def _normalize_score_grid(self, score_grid: np.ndarray) -> np.ndarray:
        """Normalize score grid with enhanced contrast"""
        normalized = np.clip(score_grid, 0, 10)
        max_score = np.max(normalized)
        
        # Enhance contrast for low scores
        if max_score < 2.0:
            normalized = (normalized / max_score) * 5.0
        elif max_score < 5.0:
            normalized = (normalized / max_score) * 7.0
            
        return normalized

    def _determine_contour_levels(self, scores: np.ndarray) -> np.ndarray:
        """Determine appropriate contour levels"""
        max_score = np.max(scores)
        if max_score <= 5.0:
            return np.linspace(0, 5, self.config.contour_levels)
        elif max_score <= 7.0:
            return np.linspace(0, 7, self.config.contour_levels)
        else:
            return np.linspace(0, 10, self.config.contour_levels)

    def _add_enhanced_colorbar(self, fig: plt.Figure, ax: plt.Axes,
                             im: plt.cm.ScalarMappable,
                             scores: np.ndarray) -> plt.colorbar.Colorbar:
        """Add enhanced colorbar with descriptive labels"""
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Deer Activity Score',
                      fontsize=self.config.label_fontsize,
                      fontweight='bold')
        
        max_level = np.max(scores)
        if max_level <= 5:
            cbar.set_ticks([0, 1, 2, 3, 4, 5])
            cbar.set_ticklabels(['None\n(0)', 'Very Low\n(1)', 'Low\n(2)',
                               'Moderate\n(3)', 'Good\n(4)', 'High\n(5)'])
        elif max_level <= 7:
            cbar.set_ticks([0, 1, 2, 3, 4, 5, 6, 7])
            cbar.set_ticklabels(['None\n(0)', 'Very Low\n(1)', 'Low\n(2)',
                               'Moderate\n(3)', 'Good\n(4)', 'High\n(5)',
                               'Very High\n(6)', 'Excellent\n(7)'])
        else:
            cbar.set_ticks([0, 2, 4, 6, 8, 10])
            cbar.set_ticklabels(['Very Low\n(0-1)', 'Low\n(2-3)',
                               'Moderate\n(4-5)', 'Good\n(6-7)',
                               'High\n(8-9)', 'Excellent\n(10)'])
        
        return cbar

    def _enhance_plot_appearance(self, ax: plt.Axes, title: str, description: str):
        """Enhance plot appearance with title and labels"""
        ax.set_title(f'{title}\n{description}',
                    fontsize=self.config.title_fontsize,
                    fontweight='bold',
                    pad=20)
        ax.set_xlabel('Grid East-West',
                     fontsize=self.config.label_fontsize)
        ax.set_ylabel('Grid North-South',
                     fontsize=self.config.label_fontsize)

    def _add_score_statistics(self, ax: plt.Axes, scores: np.ndarray):
        """Add score statistics to plot"""
        actual_max = np.max(scores)
        actual_avg = np.mean(scores)
        high_score_percent = np.sum(scores >= np.percentile(scores, 80)) / scores.size * 100
        
        stats_text = (f'Original Max: {actual_max:.1f}\n'
                     f'Original Avg: {actual_avg:.1f}\n'
                     f'Top 20% Areas: {high_score_percent:.1f}%')
        
        ax.text(0.02, 0.98, stats_text,
                transform=ax.transAxes,
                bbox=dict(boxstyle='round',
                         facecolor='white',
                         alpha=0.8),
                verticalalignment='top',
                fontsize=self.config.annotation_fontsize)

    def _add_feature_markers(self, ax: plt.Axes,
                           features: Dict[str, Any],
                           elevation_grid: np.ndarray):
        """Add feature markers to 3D plot"""
        marker_styles = {
            'saddle': ('o', 'red'),
            'ridge': ('^', 'blue'),
            'drainage': ('s', 'green'),
            'bench': ('D', 'purple')
        }
        
        for feature_type, features_list in features.items():
            if feature_type in marker_styles:
                marker, color = marker_styles[feature_type]
                for feature in features_list:
                    x, y = feature['grid_position']
                    z = elevation_grid[x, y]
                    ax.scatter([x], [y], [z],
                             marker=marker,
                             c=color,
                             s=100,
                             label=feature_type.capitalize())

    def _plot_features(self, ax: plt.Axes, features: Dict[str, Any]):
        """Plot features on 2D map"""
        marker_styles = {
            'saddle': {'marker': 'o', 'color': 'red', 'label': 'Saddle'},
            'ridge': {'marker': '^', 'color': 'blue', 'label': 'Ridge'},
            'drainage': {'marker': 's', 'color': 'green', 'label': 'Drainage'},
            'bench': {'marker': 'D', 'color': 'purple', 'label': 'Bench'},
            'funnel': {'marker': '*', 'color': 'orange', 'label': 'Funnel'}
        }
        
        for feature_type, features_list in features.items():
            if feature_type in marker_styles:
                style = marker_styles[feature_type]
                x = [f['grid_position'][0] for f in features_list]
                y = [f['grid_position'][1] for f in features_list]
                ax.scatter(x, y, **style)

    def _add_feature_legend(self, ax: plt.Axes):
        """Add feature legend to plot"""
        ax.legend(loc='upper right',
                 bbox_to_anchor=(1.15, 1.0),
                 fontsize=self.config.annotation_fontsize)

    def _figure_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64 string"""
        buffer = BytesIO()
        fig.savefig(buffer,
                   format='png',
                   dpi=self.config.dpi,
                   bbox_inches='tight',
                   facecolor='white',
                   edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        return image_base64

    def _create_error_visualization(self) -> str:
        """Create simple error visualization"""
        try:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5,
                   "Error creating visualization",
                   ha='center',
                   va='center',
                   fontsize=14)
            ax.set_axis_off()
            return self._figure_to_base64(fig)
        except Exception:
            # If all else fails, return empty string
            return ""
        finally:
            plt.close()

# Global visualization system instance
_visualization_system = None

def get_visualization_system() -> VisualizationSystem:
    """Get or create the global visualization system instance"""
    global _visualization_system
    if _visualization_system is None:
        _visualization_system = VisualizationSystem()
    return _visualization_system
