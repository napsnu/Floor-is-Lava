import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import time


class MultiPersonTracker:
    def __init__(self, max_disappeared: int = 30, max_distance: float = 50.0):
        """
        Multi-person tracker for pose detection results.
        
        Args:
            max_disappeared: Maximum frames a person can be missing before removal
            max_distance: Maximum distance for matching detections
        """
        self.next_id = 0
        self.objects = {}  # id -> track data
        self.disappeared = {}  # id -> frames since last seen
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
    
    def update(self, detections: List[Dict]) -> Dict[int, Dict]:
        """
        Update tracker with new detections.
        
        Args:
            detections: List of detection dictionaries from pose tracker
            
        Returns:
            Dictionary mapping person_id to track data
        """
        # If no detections, increment disappeared counters
        if len(detections) == 0:
            for person_id in list(self.disappeared.keys()):
                self.disappeared[person_id] += 1
                if self.disappeared[person_id] > self.max_disappeared:
                    self._deregister(person_id)
            return self.objects
        
        # If no existing objects, register all detections
        if len(self.objects) == 0:
            for detection in detections:
                self._register(detection)
        else:
            # Match detections to existing objects
            object_centroids = np.array([obj['centroid'] for obj in self.objects.values()])
            detection_centroids = self._get_detection_centroids(detections)
            
            # Compute distance matrix
            D = np.linalg.norm(object_centroids[:, np.newaxis] - detection_centroids, axis=2)
            
            # Find optimal assignment using simple greedy approach
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            
            used_row_indices = set()
            used_col_indices = set()
            
            for (row, col) in zip(rows, cols):
                if row in used_row_indices or col in used_col_indices:
                    continue
                
                if D[row, col] > self.max_distance:
                    continue
                
                person_id = list(self.objects.keys())[row]
                self.objects[person_id]['last_det'] = detections[col]
                self.objects[person_id]['centroid'] = detection_centroids[col]
                self.disappeared[person_id] = 0
                
                used_row_indices.add(row)
                used_col_indices.add(col)
            
            # Handle unmatched detections and objects
            unused_rows = set(range(0, D.shape[0])).difference(used_row_indices)
            unused_cols = set(range(0, D.shape[1])).difference(used_col_indices)
            
            # If more objects than detections, mark unmatched objects as disappeared
            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    person_id = list(self.objects.keys())[row]
                    self.disappeared[person_id] += 1
                    if self.disappeared[person_id] > self.max_disappeared:
                        self._deregister(person_id)
            
            # If more detections than objects, register new objects
            else:
                for col in unused_cols:
                    self._register(detections[col])
        
        return self.objects
    
    def _register(self, detection: Dict):
        """Register a new person"""
        person_id = self.next_id
        self.next_id += 1
        
        centroid = self._get_centroid(detection)
        self.objects[person_id] = {
            'last_det': detection,
            'centroid': centroid
        }
        self.disappeared[person_id] = 0
    
    def _deregister(self, person_id: int):
        """Deregister a person"""
        del self.objects[person_id]
        del self.disappeared[person_id]
    
    def _get_centroid(self, detection: Dict) -> Tuple[float, float]:
        """Calculate centroid from detection"""
        left_pixel = detection['left']['pixel']
        right_pixel = detection['right']['pixel']
        return (
            (left_pixel[0] + right_pixel[0]) / 2.0,
            (left_pixel[1] + right_pixel[1]) / 2.0
        )
    
    def _get_detection_centroids(self, detections: List[Dict]) -> np.ndarray:
        """Get centroids for all detections"""
        centroids = []
        for detection in detections:
            centroid = self._get_centroid(detection)
            centroids.append(centroid)
        return np.array(centroids)






