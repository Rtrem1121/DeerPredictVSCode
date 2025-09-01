import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, Clock, MapPin, Thermometer, TrendingUp } from 'lucide-react';
import React from 'react';

// Types for thermal analysis data
interface ThermalAnalysisData {
    thermal_conditions: {
        is_active: boolean;
        direction: string;
        strength_scale: number;
        timing_analysis?: {
            optimal_timing: string;
            current_status: string;
            time_to_optimal?: number;
        };
    };
    thermal_advantages: {
        optimal_timing: string;
        hunting_windows?: string[];
        thermal_strength?: string;
    };
    thermal_locations: string[];
    timing_recommendations?: {
        best_periods: string[];
        avoid_periods: string[];
        current_rating: number;
    };
}

interface ThermalAnalysisComponentProps {
    thermalAnalysis: ThermalAnalysisData | null;
    isLoading?: boolean;
}

const ThermalAnalysisComponent: React.FC<ThermalAnalysisComponentProps> = ({
    thermalAnalysis,
    isLoading = false
}) => {
    if (isLoading) {
        return (
            <Card className="w-full">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Thermometer className="h-5 w-5" />
                        Thermal Analysis
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

    if (!thermalAnalysis) {
        return (
            <Card className="w-full">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Thermometer className="h-5 w-5" />
                        Thermal Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-500">No thermal analysis data available</p>
                </CardContent>
            </Card>
        );
    }

    const getThermalStatusColor = (isActive: boolean, strength: number): string => {
        if (!isActive) return 'bg-gray-100 text-gray-800 border-gray-200';
        if (strength >= 7) return 'bg-orange-100 text-orange-800 border-orange-200';
        if (strength >= 5) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-blue-100 text-blue-800 border-blue-200';
    };

    const getThermalStrengthLabel = (strength: number): string => {
        if (strength >= 8) return 'Very Strong';
        if (strength >= 6) return 'Strong';
        if (strength >= 4) return 'Moderate';
        if (strength >= 2) return 'Weak';
        return 'Minimal';
    };

    const getTimingRatingColor = (rating: number): string => {
        if (rating >= 8) return 'bg-green-100 text-green-800 border-green-200';
        if (rating >= 6) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        return 'bg-red-100 text-red-800 border-red-200';
    };

    const formatDirection = (direction: string): string => {
        return direction.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    };

    const formatOptimalTiming = (timing: string): string => {
        return timing.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    };

    return (
        <Card className="w-full">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Thermometer className="h-5 w-5" />
                    Thermal Analysis
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                {/* Current Thermal Status */}
                <div className="space-y-3">
                    <h4 className="font-semibold text-sm text-gray-700">Current Thermal Conditions</h4>
                    <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <Badge
                                    className={`${getThermalStatusColor(
                                        thermalAnalysis.thermal_conditions.is_active,
                                        thermalAnalysis.thermal_conditions.strength_scale
                                    )} border px-3 py-2`}
                                >
                                    {thermalAnalysis.thermal_conditions.is_active ? 'Active' : 'Inactive'}
                                </Badge>
                                {thermalAnalysis.thermal_conditions.is_active && (
                                    <span className="text-sm font-medium">
                                        {getThermalStrengthLabel(thermalAnalysis.thermal_conditions.strength_scale)}
                                    </span>
                                )}
                            </div>
                            <div className="text-right">
                                <div className="text-sm text-gray-600">Strength</div>
                                <div className="font-semibold">
                                    {thermalAnalysis.thermal_conditions.strength_scale.toFixed(1)}/10
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span className="text-gray-600">Direction:</span>
                                <div className="font-medium">
                                    {formatDirection(thermalAnalysis.thermal_conditions.direction)}
                                </div>
                            </div>
                            {thermalAnalysis.thermal_conditions.timing_analysis && (
                                <div>
                                    <span className="text-gray-600">Current Status:</span>
                                    <div className="font-medium">
                                        {formatOptimalTiming(thermalAnalysis.thermal_conditions.timing_analysis.current_status)}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Optimal Timing */}
                <div className="space-y-3">
                    <h4 className="font-semibold text-sm text-gray-700">Optimal Hunting Times</h4>
                    <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 mb-2">
                            <Clock className="h-4 w-4 text-green-600" />
                            <span className="font-medium text-green-800">
                                {formatOptimalTiming(thermalAnalysis.thermal_advantages.optimal_timing)}
                            </span>
                        </div>

                        {thermalAnalysis.thermal_advantages.hunting_windows &&
                            thermalAnalysis.thermal_advantages.hunting_windows.length > 0 && (
                                <div className="mt-3">
                                    <span className="text-sm text-green-700">Prime Windows:</span>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {thermalAnalysis.thermal_advantages.hunting_windows.map((window, index) => (
                                            <Badge key={index} variant="outline" className="bg-green-100 text-green-700 border-green-300">
                                                {window}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}

                        {thermalAnalysis.thermal_advantages.thermal_strength && (
                            <div className="mt-2 text-sm text-green-700">
                                <span className="font-medium">Strength: </span>
                                {thermalAnalysis.thermal_advantages.thermal_strength}
                            </div>
                        )}
                    </div>
                </div>

                {/* Timing Recommendations */}
                {thermalAnalysis.timing_recommendations && (
                    <div className="space-y-3">
                        <h4 className="font-semibold text-sm text-gray-700">Timing Recommendations</h4>
                        <div className="space-y-3">
                            {/* Current Rating */}
                            <div className="flex items-center gap-3">
                                <span className="text-sm text-gray-600">Current Timing Rating:</span>
                                <Badge
                                    className={`${getTimingRatingColor(thermalAnalysis.timing_recommendations.current_rating)} border`}
                                >
                                    {thermalAnalysis.timing_recommendations.current_rating.toFixed(1)}/10
                                </Badge>
                            </div>

                            {/* Best Periods */}
                            {thermalAnalysis.timing_recommendations.best_periods.length > 0 && (
                                <div>
                                    <span className="text-sm text-gray-600 block mb-2">Best Periods:</span>
                                    <div className="flex flex-wrap gap-2">
                                        {thermalAnalysis.timing_recommendations.best_periods.map((period, index) => (
                                            <Badge key={index} className="bg-green-100 text-green-800 border-green-200">
                                                <TrendingUp className="h-3 w-3 mr-1" />
                                                {period}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Avoid Periods */}
                            {thermalAnalysis.timing_recommendations.avoid_periods.length > 0 && (
                                <div>
                                    <span className="text-sm text-gray-600 block mb-2">Avoid Periods:</span>
                                    <div className="flex flex-wrap gap-2">
                                        {thermalAnalysis.timing_recommendations.avoid_periods.map((period, index) => (
                                            <Badge key={index} className="bg-red-100 text-red-800 border-red-200">
                                                <AlertCircle className="h-3 w-3 mr-1" />
                                                {period}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Thermal Locations */}
                {thermalAnalysis.thermal_locations && thermalAnalysis.thermal_locations.length > 0 && (
                    <div className="space-y-3">
                        <h4 className="font-semibold text-sm text-gray-700">Thermal Activity Zones</h4>
                        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                            <div className="grid grid-cols-1 gap-2">
                                {thermalAnalysis.thermal_locations.map((location, index) => (
                                    <div key={index} className="flex items-center gap-2">
                                        <MapPin className="h-4 w-4 text-blue-600" />
                                        <span className="text-sm capitalize">
                                            {formatDirection(location)}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Time to Optimal Alert */}
                {thermalAnalysis.thermal_conditions.timing_analysis?.time_to_optimal && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-amber-600" />
                            <span className="text-sm font-medium text-amber-800">Timing Alert</span>
                        </div>
                        <p className="text-sm text-amber-700 mt-1">
                            Optimal thermal conditions in {thermalAnalysis.thermal_conditions.timing_analysis.time_to_optimal} minutes
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default ThermalAnalysisComponent;
