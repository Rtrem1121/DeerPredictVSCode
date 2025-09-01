import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, Brain, ChevronDown, ChevronUp, Database, Target, Wind } from 'lucide-react';
import React, { useState } from 'react';
import ThermalAnalysisComponent from './ThermalAnalysisComponent';
import WindAnalysisComponent from './WindAnalysisComponent';

// Types for comprehensive analysis data
interface AnalysisMetadata {
    analysis_timestamp: string;
    completion_percentage: number;
    analyzer_version: string;
    total_components: number;
    completed_components: number;
}

interface CriteriaAnalysis {
    bedding_criteria: Record<string, any>;
    stand_criteria: Record<string, any>;
    feeding_criteria: Record<string, any>;
    threshold_parameters: Record<string, any>;
    criteria_summary: {
        total_criteria: number;
        met_criteria: number;
        compliance_percentage: number;
    };
}

interface DataSourceAnalysis {
    satellite_data: {
        resolution: string;
        coverage_area: number;
        acquisition_date: string;
        quality_score: number;
    };
    lidar_data?: {
        point_density: number;
        vertical_accuracy: string;
        coverage_percentage: number;
    };
    weather_data: {
        source: string;
        update_frequency: string;
        current_conditions: Record<string, any>;
    };
    gis_layers: string[];
    data_quality_summary: {
        overall_quality: number;
        data_freshness: number;
        completeness: number;
    };
}

interface AlgorithmAnalysis {
    prediction_algorithms: string[];
    feature_engineering: {
        terrain_features: number;
        vegetation_features: number;
        hydrological_features: number;
        anthropogenic_features: number;
    };
    model_parameters: Record<string, any>;
    algorithm_summary: {
        primary_algorithm: string;
        confidence_factors: string[];
        processing_time: number;
    };
}

interface ScoringAnalysis {
    suitability_scores: {
        bedding_zones: {
            average_score: number;
            score_range: [number, number];
            high_quality_zones: number;
        };
        stand_locations: {
            average_score: number;
            score_range: [number, number];
            optimal_stands: number;
        };
        feeding_areas: {
            average_score: number;
            score_range: [number, number];
            prime_feeding_spots: number;
        };
    };
    confidence_metrics: {
        overall_confidence: number;
        prediction_reliability: number;
        data_confidence: number;
    };
}

interface ComprehensiveAnalysis {
    analysis_metadata: AnalysisMetadata;
    criteria_analysis: CriteriaAnalysis | null;
    data_source_analysis: DataSourceAnalysis | null;
    algorithm_analysis: AlgorithmAnalysis | null;
    scoring_analysis: ScoringAnalysis | null;
    wind_analysis: any | null;  // From WindAnalysisComponent
    thermal_analysis: any | null;  // From ThermalAnalysisComponent
}

interface AnalysisDisplayContainerProps {
    comprehensiveAnalysis: ComprehensiveAnalysis | null;
    isLoading?: boolean;
    isExpanded?: boolean;
    onToggleExpanded?: () => void;
}

const AnalysisDisplayContainer: React.FC<AnalysisDisplayContainerProps> = ({
    comprehensiveAnalysis,
    isLoading = false,
    isExpanded = false,
    onToggleExpanded
}) => {
    const [activeTab, setActiveTab] = useState('overview');

    if (isLoading) {
        return (
            <Card className="w-full mt-4">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        Detailed Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="animate-pulse space-y-4">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-8 bg-gray-200 rounded"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!comprehensiveAnalysis) {
        return (
            <Card className="w-full mt-4">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        Detailed Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-500">No detailed analysis data available</p>
                </CardContent>
            </Card>
        );
    }

    const getCompletionColor = (percentage: number): string => {
        if (percentage >= 80) return 'bg-green-100 text-green-800 border-green-200';
        if (percentage >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-red-100 text-red-800 border-red-200';
    };

    const getQualityColor = (score: number): string => {
        if (score >= 8) return 'bg-green-100 text-green-800 border-green-200';
        if (score >= 6) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-red-100 text-red-800 border-red-200';
    };

    const formatTimestamp = (timestamp: string): string => {
        try {
            return new Date(timestamp).toLocaleString();
        } catch {
            return timestamp;
        }
    };

    const CompactOverview = () => (
        <div className="space-y-4">
            {/* Analysis Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                    <div className="text-sm font-medium text-blue-800">Analysis Status</div>
                    <div className="flex items-center gap-2 mt-1">
                        <Badge className={`${getCompletionColor(comprehensiveAnalysis.analysis_metadata.completion_percentage)} border`}>
                            {comprehensiveAnalysis.analysis_metadata.completion_percentage.toFixed(1)}%
                        </Badge>
                        <span className="text-sm text-blue-700">
                            {comprehensiveAnalysis.analysis_metadata.completed_components}/{comprehensiveAnalysis.analysis_metadata.total_components} complete
                        </span>
                    </div>
                </div>

                {comprehensiveAnalysis.data_source_analysis && (
                    <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                        <div className="text-sm font-medium text-green-800">Data Quality</div>
                        <div className="flex items-center gap-2 mt-1">
                            <Badge className={`${getQualityColor(comprehensiveAnalysis.data_source_analysis.data_quality_summary.overall_quality)} border`}>
                                {comprehensiveAnalysis.data_source_analysis.data_quality_summary.overall_quality.toFixed(1)}/10
                            </Badge>
                            <span className="text-sm text-green-700">Overall quality</span>
                        </div>
                    </div>
                )}

                {comprehensiveAnalysis.scoring_analysis && (
                    <div className="bg-purple-50 p-3 rounded-lg border border-purple-200">
                        <div className="text-sm font-medium text-purple-800">Confidence</div>
                        <div className="flex items-center gap-2 mt-1">
                            <Badge className={`${getQualityColor(comprehensiveAnalysis.scoring_analysis.confidence_metrics.overall_confidence)} border`}>
                                {comprehensiveAnalysis.scoring_analysis.confidence_metrics.overall_confidence.toFixed(1)}/10
                            </Badge>
                            <span className="text-sm text-purple-700">Overall confidence</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Quick Stats */}
            {comprehensiveAnalysis.criteria_analysis && (
                <div className="bg-gray-50 p-3 rounded-lg border border-gray-200">
                    <div className="text-sm font-medium text-gray-800 mb-2">Criteria Compliance</div>
                    <div className="text-lg font-semibold text-gray-900">
                        {comprehensiveAnalysis.criteria_analysis.criteria_summary.met_criteria}/
                        {comprehensiveAnalysis.criteria_analysis.criteria_summary.total_criteria} criteria met
                        <span className="text-sm font-normal text-gray-600 ml-2">
                            ({comprehensiveAnalysis.criteria_analysis.criteria_summary.compliance_percentage.toFixed(1)}%)
                        </span>
                    </div>
                </div>
            )}
        </div>
    );

    const CriteriaTab = () => (
        <div className="space-y-6">
            {comprehensiveAnalysis.criteria_analysis ? (
                <>
                    {/* Criteria Summary */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                            <div className="text-sm font-medium text-blue-800">Bedding Criteria</div>
                            <div className="mt-2 space-y-1">
                                {Object.entries(comprehensiveAnalysis.criteria_analysis.bedding_criteria).slice(0, 3).map(([key, value]) => (
                                    <div key={key} className="text-xs">
                                        <span className="text-blue-600">{key.replace('_', ' ')}: </span>
                                        <span className="font-medium">{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                            <div className="text-sm font-medium text-green-800">Stand Criteria</div>
                            <div className="mt-2 space-y-1">
                                {Object.entries(comprehensiveAnalysis.criteria_analysis.stand_criteria).slice(0, 3).map(([key, value]) => (
                                    <div key={key} className="text-xs">
                                        <span className="text-green-600">{key.replace('_', ' ')}: </span>
                                        <span className="font-medium">{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                            <div className="text-sm font-medium text-orange-800">Feeding Criteria</div>
                            <div className="mt-2 space-y-1">
                                {Object.entries(comprehensiveAnalysis.criteria_analysis.feeding_criteria).slice(0, 3).map(([key, value]) => (
                                    <div key={key} className="text-xs">
                                        <span className="text-orange-600">{key.replace('_', ' ')}: </span>
                                        <span className="font-medium">{String(value)}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Compliance Summary */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="font-semibold text-gray-800 mb-3">Compliance Summary</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <span className="text-sm text-gray-600">Total Criteria:</span>
                                <div className="font-semibold">{comprehensiveAnalysis.criteria_analysis.criteria_summary.total_criteria}</div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-600">Met Criteria:</span>
                                <div className="font-semibold">{comprehensiveAnalysis.criteria_analysis.criteria_summary.met_criteria}</div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-600">Compliance Rate:</span>
                                <div className="font-semibold">{comprehensiveAnalysis.criteria_analysis.criteria_summary.compliance_percentage.toFixed(1)}%</div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <p className="text-gray-500">No criteria analysis data available</p>
            )}
        </div>
    );

    const DataSourcesTab = () => (
        <div className="space-y-6">
            {comprehensiveAnalysis.data_source_analysis ? (
                <>
                    {/* Data Sources Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Satellite Data */}
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                            <div className="flex items-center gap-2 mb-3">
                                <Database className="h-4 w-4 text-blue-600" />
                                <span className="font-medium text-blue-800">Satellite Data</span>
                            </div>
                            <div className="space-y-2 text-sm">
                                <div>
                                    <span className="text-blue-600">Resolution: </span>
                                    <span className="font-medium">{comprehensiveAnalysis.data_source_analysis.satellite_data.resolution}</span>
                                </div>
                                <div>
                                    <span className="text-blue-600">Coverage: </span>
                                    <span className="font-medium">{comprehensiveAnalysis.data_source_analysis.satellite_data.coverage_area} km²</span>
                                </div>
                                <div>
                                    <span className="text-blue-600">Quality: </span>
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.data_source_analysis.satellite_data.quality_score)} border text-xs`}>
                                        {comprehensiveAnalysis.data_source_analysis.satellite_data.quality_score.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                        </div>

                        {/* Weather Data */}
                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                            <div className="flex items-center gap-2 mb-3">
                                <Wind className="h-4 w-4 text-green-600" />
                                <span className="font-medium text-green-800">Weather Data</span>
                            </div>
                            <div className="space-y-2 text-sm">
                                <div>
                                    <span className="text-green-600">Source: </span>
                                    <span className="font-medium">{comprehensiveAnalysis.data_source_analysis.weather_data.source}</span>
                                </div>
                                <div>
                                    <span className="text-green-600">Updates: </span>
                                    <span className="font-medium">{comprehensiveAnalysis.data_source_analysis.weather_data.update_frequency}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Data Quality Summary */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="font-semibold text-gray-800 mb-3">Data Quality Summary</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <span className="text-sm text-gray-600">Overall Quality:</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.data_source_analysis.data_quality_summary.overall_quality)} border`}>
                                        {comprehensiveAnalysis.data_source_analysis.data_quality_summary.overall_quality.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-600">Data Freshness:</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.data_source_analysis.data_quality_summary.data_freshness)} border`}>
                                        {comprehensiveAnalysis.data_source_analysis.data_quality_summary.data_freshness.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-600">Completeness:</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.data_source_analysis.data_quality_summary.completeness)} border`}>
                                        {comprehensiveAnalysis.data_source_analysis.data_quality_summary.completeness.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* GIS Layers */}
                    {comprehensiveAnalysis.data_source_analysis.gis_layers.length > 0 && (
                        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                            <h4 className="font-semibold text-purple-800 mb-3">GIS Layers Used</h4>
                            <div className="flex flex-wrap gap-2">
                                {comprehensiveAnalysis.data_source_analysis.gis_layers.map((layer, index) => (
                                    <Badge key={index} variant="outline" className="bg-purple-100 text-purple-700 border-purple-300">
                                        {layer}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <p className="text-gray-500">No data source analysis available</p>
            )}
        </div>
    );

    const AlgorithmsTab = () => (
        <div className="space-y-6">
            {comprehensiveAnalysis.algorithm_analysis ? (
                <>
                    {/* Algorithm Summary */}
                    <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                        <div className="flex items-center gap-2 mb-3">
                            <Brain className="h-4 w-4 text-indigo-600" />
                            <span className="font-medium text-indigo-800">Primary Algorithm</span>
                        </div>
                        <div className="text-lg font-semibold text-indigo-900">
                            {comprehensiveAnalysis.algorithm_analysis.algorithm_summary.primary_algorithm}
                        </div>
                        <div className="text-sm text-indigo-700 mt-1">
                            Processing time: {comprehensiveAnalysis.algorithm_analysis.algorithm_summary.processing_time}ms
                        </div>
                    </div>

                    {/* Feature Engineering */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="font-semibold text-gray-800 mb-3">Feature Engineering</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center">
                                <div className="text-2xl font-bold text-green-600">
                                    {comprehensiveAnalysis.algorithm_analysis.feature_engineering.terrain_features}
                                </div>
                                <div className="text-sm text-gray-600">Terrain Features</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-blue-600">
                                    {comprehensiveAnalysis.algorithm_analysis.feature_engineering.vegetation_features}
                                </div>
                                <div className="text-sm text-gray-600">Vegetation Features</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-cyan-600">
                                    {comprehensiveAnalysis.algorithm_analysis.feature_engineering.hydrological_features}
                                </div>
                                <div className="text-sm text-gray-600">Hydrological Features</div>
                            </div>
                            <div className="text-center">
                                <div className="text-2xl font-bold text-orange-600">
                                    {comprehensiveAnalysis.algorithm_analysis.feature_engineering.anthropogenic_features}
                                </div>
                                <div className="text-sm text-gray-600">Anthropogenic Features</div>
                            </div>
                        </div>
                    </div>

                    {/* Confidence Factors */}
                    {comprehensiveAnalysis.algorithm_analysis.algorithm_summary.confidence_factors.length > 0 && (
                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                            <h4 className="font-semibold text-green-800 mb-3">Confidence Factors</h4>
                            <div className="flex flex-wrap gap-2">
                                {comprehensiveAnalysis.algorithm_analysis.algorithm_summary.confidence_factors.map((factor, index) => (
                                    <Badge key={index} className="bg-green-100 text-green-800 border-green-200">
                                        {factor}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            ) : (
                <p className="text-gray-500">No algorithm analysis data available</p>
            )}
        </div>
    );

    const ScoringTab = () => (
        <div className="space-y-6">
            {comprehensiveAnalysis.scoring_analysis ? (
                <>
                    {/* Suitability Scores */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Bedding Zones */}
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                            <div className="flex items-center gap-2 mb-3">
                                <Target className="h-4 w-4 text-blue-600" />
                                <span className="font-medium text-blue-800">Bedding Zones</span>
                            </div>
                            <div className="space-y-2">
                                <div>
                                    <span className="text-sm text-blue-600">Average Score:</span>
                                    <div className="font-semibold">{comprehensiveAnalysis.scoring_analysis.suitability_scores.bedding_zones.average_score.toFixed(1)}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-blue-600">High Quality Zones:</span>
                                    <div className="font-semibold">{comprehensiveAnalysis.scoring_analysis.suitability_scores.bedding_zones.high_quality_zones}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-blue-600">Score Range:</span>
                                    <div className="font-medium text-sm">
                                        {comprehensiveAnalysis.scoring_analysis.suitability_scores.bedding_zones.score_range[0].toFixed(1)} -
                                        {comprehensiveAnalysis.scoring_analysis.suitability_scores.bedding_zones.score_range[1].toFixed(1)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Stand Locations */}
                        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                            <div className="flex items-center gap-2 mb-3">
                                <Target className="h-4 w-4 text-green-600" />
                                <span className="font-medium text-green-800">Stand Locations</span>
                            </div>
                            <div className="space-y-2">
                                <div>
                                    <span className="text-sm text-green-600">Average Score:</span>
                                    <div className="font-semibold">{comprehensiveAnalysis.scoring_analysis.suitability_scores.stand_locations.average_score.toFixed(1)}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-green-600">Optimal Stands:</span>
                                    <div className="font-semibold">{comprehensiveAnalysis.scoring_analysis.suitability_scores.stand_locations.optimal_stands}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-green-600">Score Range:</span>
                                    <div className="font-medium text-sm">
                                        {comprehensiveAnalysis.scoring_analysis.suitability_scores.stand_locations.score_range[0].toFixed(1)} -
                                        {comprehensiveAnalysis.scoring_analysis.suitability_scores.stand_locations.score_range[1].toFixed(1)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Feeding Areas */}
                        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                            <div className="flex items-center gap-2 mb-3">
                                <Target className="h-4 w-4 text-orange-600" />
                                <span className="font-medium text-orange-800">Feeding Areas</span>
                            </div>
                            <div className="space-y-2">
                                <div>
                                    <span className="text-sm text-orange-600">Average Score:</span>
                                    <div className="font-semibold">{comprehensiveAnalysis.scoring_analysis.suitability_scores.feeding_areas.average_score.toFixed(1)}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-orange-600">Prime Spots:</span>
                                    <div className="font-semibold">{comprehensiveAnalysis.scoring_analysis.suitability_scores.feeding_areas.prime_feeding_spots}</div>
                                </div>
                                <div>
                                    <span className="text-sm text-orange-600">Score Range:</span>
                                    <div className="font-medium text-sm">
                                        {comprehensiveAnalysis.scoring_analysis.suitability_scores.feeding_areas.score_range[0].toFixed(1)} -
                                        {comprehensiveAnalysis.scoring_analysis.suitability_scores.feeding_areas.score_range[1].toFixed(1)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Confidence Metrics */}
                    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <h4 className="font-semibold text-gray-800 mb-3">Confidence Metrics</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <span className="text-sm text-gray-600">Overall Confidence:</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.scoring_analysis.confidence_metrics.overall_confidence)} border`}>
                                        {comprehensiveAnalysis.scoring_analysis.confidence_metrics.overall_confidence.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-600">Prediction Reliability:</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.scoring_analysis.confidence_metrics.prediction_reliability)} border`}>
                                        {comprehensiveAnalysis.scoring_analysis.confidence_metrics.prediction_reliability.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                            <div>
                                <span className="text-sm text-gray-600">Data Confidence:</span>
                                <div className="flex items-center gap-2 mt-1">
                                    <Badge className={`${getQualityColor(comprehensiveAnalysis.scoring_analysis.confidence_metrics.data_confidence)} border`}>
                                        {comprehensiveAnalysis.scoring_analysis.confidence_metrics.data_confidence.toFixed(1)}/10
                                    </Badge>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <p className="text-gray-500">No scoring analysis data available</p>
            )}
        </div>
    );

    return (
        <Card className="w-full mt-4">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        Detailed Prediction Analysis
                    </CardTitle>
                    {onToggleExpanded && (
                        <button
                            onClick={onToggleExpanded}
                            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
                        >
                            {isExpanded ? (
                                <>
                                    <ChevronUp className="h-4 w-4" />
                                    Collapse
                                </>
                            ) : (
                                <>
                                    <ChevronDown className="h-4 w-4" />
                                    Expand
                                </>
                            )}
                        </button>
                    )}
                </div>
                <div className="text-sm text-gray-500">
                    Analysis generated on {formatTimestamp(comprehensiveAnalysis.analysis_metadata.analysis_timestamp)}
                </div>
            </CardHeader>
            <CardContent>
                {!isExpanded ? (
                    <CompactOverview />
                ) : (
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                        <TabsList className="grid w-full grid-cols-6">
                            <TabsTrigger value="overview">Overview</TabsTrigger>
                            <TabsTrigger value="criteria">Criteria</TabsTrigger>
                            <TabsTrigger value="data">Data Sources</TabsTrigger>
                            <TabsTrigger value="algorithms">Algorithms</TabsTrigger>
                            <TabsTrigger value="scoring">Scoring</TabsTrigger>
                            <TabsTrigger value="environmental">Environmental</TabsTrigger>
                        </TabsList>

                        <TabsContent value="overview" className="mt-6">
                            <CompactOverview />
                        </TabsContent>

                        <TabsContent value="criteria" className="mt-6">
                            <CriteriaTab />
                        </TabsContent>

                        <TabsContent value="data" className="mt-6">
                            <DataSourcesTab />
                        </TabsContent>

                        <TabsContent value="algorithms" className="mt-6">
                            <AlgorithmsTab />
                        </TabsContent>

                        <TabsContent value="scoring" className="mt-6">
                            <ScoringTab />
                        </TabsContent>

                        <TabsContent value="environmental" className="mt-6">
                            <div className="space-y-6">
                                <WindAnalysisComponent
                                    windAnalysis={comprehensiveAnalysis.wind_analysis}
                                    isLoading={false}
                                />
                                <ThermalAnalysisComponent
                                    thermalAnalysis={comprehensiveAnalysis.thermal_analysis}
                                    isLoading={false}
                                />
                            </div>
                        </TabsContent>
                    </Tabs>
                )}
            </CardContent>
        </Card>
    );
};

export default AnalysisDisplayContainer;
